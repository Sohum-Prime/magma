# Tools: Empowering Agents with Capabilities

An agent is only as capable as the tools it can wield. Tools are the bridge between the LLM's reasoning abilities and the outside world, allowing it to fetch information, execute code, or interact with any API.

Magma, inspired by the developer-friendly approach of **smolagents**, makes defining tools incredibly simple and robust. You can turn any Python function into a secure, type-safe tool that your agent can reliably use, simply by adding a decorator.

## Creating Your Own Tools

There are two primary ways to create a tool: the simple decorator for stateless functions, and subclassing for more complex, stateful tools.

### 1. The `@magma.tool` Decorator (Simple Tools)

The easiest and most common way to create a tool is with the `@magma.tool` decorator. You write a standard Python function with type hints and a docstring, and Magma handles the rest.

```python
import magma

@magma.tool
def get_stock_price(ticker: str, currency: str = "USD") -> float:
    """
    Retrieves the current stock price for a given ticker symbol.
    
    Args:
        ticker (str): The stock symbol to look up (e.g., "NVDA", "GOOG").
        currency (str): The currency to return the price in. Defaults to "USD".
    """
    # In a real implementation, you would call a financial API here.
    if ticker.upper() == "NVDA":
        return 125.75
    else:
        return 999.99

# The tool is now automatically registered and available.
print(magma.registry.tools)
# > {'get_stock_price': <magma.Tool name='get_stock_price'>}
```

For the decorator to work effectively, your function must have:
1.  **A clear name** (`get_stock_price`). This becomes the tool's identifier.
2.  **Type-hinted parameters** (`ticker: str`). This allows Magma to generate a precise schema.
3.  **A descriptive docstring**. The LLM uses this description to understand *what the tool does* and *when to use it*. The `Args` section is crucial for explaining the parameters.

### 2. Complex Tools with State (`magma.Tool` Class)

For tools that require shared state, initialization logic, or multiple methods, you can subclass `magma.Tool` directly. This pattern is useful for things like database connections or API clients.

```python
import magma
import os

class DatabaseTool(magma.Tool):
    def __init__(self, connection_string: str):
        # Expensive setup can happen here
        self.connection = self._connect_to_db(connection_string)
        
        # We must call super().__init__() to define the tool's runtime properties
        super().__init__(
            name="sql_executor",
            func=self.invoke, # Point to the method that will be executed
            description="Executes a SQL query against the company database.",
            params=self._extract_params_from_invoke()
        )

    def _connect_to_db(self, conn_str):
        # ... logic to establish a database connection ...
        print("Database connection established.")
        return "DUMMY_CONNECTION"

    def invoke(self, query: str) -> str:
        """
        The main method to execute a query.
        
        Args:
            query (str): The SQL query to execute.
        """
        # ... logic to run query using self.connection ...
        return f"Executed query: '{query}'. Result: 1 row affected."

    def _extract_params_from_invoke(self):
        # Helper to introspect the `invoke` method for schema generation
        # In a real implementation, this logic would be more robust
        return {"query": {"type": str, "description": "The SQL query to execute."}}

# Instantiate your custom tool class
db_tool = DatabaseTool(connection_string=os.environ.get("DB_URL", "dummy_string"))
```
When subclassing, Magma uses the `name`, `description`, `func`, and `params` passed to `super().__init__` to register the tool and generate its schema.

## How It Works: The Magic Behind the Scenes

When you create a tool, Magma performs a powerful "dual-creation" process to bridge the gap between your Python code and the BAML-powered LLM interaction:

1.  **Introspection:** The decorator or `__init__` method gathers your function's signature, type hints, and docstring.
2.  **Execution Object:** It creates a standardized `magma.Tool` object in memory. This object holds the actual Python code to be **executed** by the agent when the tool is called.
3.  **Schema Generation:** Simultaneously, it generates a BAML `class` definition as a string. For the `get_stock_price` example, it would generate:
    ```baml
    // Description is automatically extracted from the docstring.
    class get_stock_price @description("Retrieves the current stock price...") {
      ticker string @description("The stock symbol to look up...")
      currency string @description("The currency to return the price in...")
    }
    ```
4.  **Runtime Injection:** When a `magma.Prompt` is executed, the `magma.Agent` gathers all registered tool schemas and uses BAML's `TypeBuilder` to inject them into the prompt. This makes the LLM aware of the exact tools and arguments available for that specific call, ensuring a type-safe and reliable function call.

## Leveraging Pre-Built Tools & Collections

You don't have to build every tool from scratch. Magma provides wrappers to easily import tools from other popular ecosystems.

#### LangChain Tools
Easily convert a tool from the extensive LangChain ecosystem.
```python
from langchain.agents import load_tools as load_lc_tools

# Load a LangChain tool
lc_search_tool = load_lc_tools(["serpapi"])[0]

# Wrap it for Magma
search_tool = magma.Tool.from_langchain(lc_search_tool)
```

#### Hugging Face Hub Tools
Load any `magma`-compatible tool directly from a Hugging Face Space.
> **Security Note:** Loading a tool from the Hub executes code from the internet. Only load tools from sources you trust and set `trust_remote_code=True`.
```python
import magma

# Load a tool from a public Space repository
image_generator = magma.Tool.from_hub(
    "magma-community/stable-diffusion-tool",
    trust_remote_code=True
)
```

#### Gradio Spaces as Tools
Turn any public Gradio Space into a usable tool, even if it wasn't built for `magma`.
```python
import magma

# Wrap a Gradio Space that generates images
flux_schnell = magma.Tool.from_space(
    space_id="black-forest-labs/FLUX.1-schnell",
    name="image_generator",
    description="Generates an image from a text prompt using the FLUX.1 model."
)
```

#### Tool Collections from the Hub
You can load entire collections of tools from the Hugging Face Hub using `ToolCollection`.
```python
from magma.tools import ToolCollection

# Load a curated collection of diffusion tools
image_tools = ToolCollection.from_hub(
    "huggingface-tools/diffusion-tools",
    trust_remote_code=True
)

# The .tools attribute holds a list of magma.Tool objects
# agent = magma.Agent(state=..., tools=image_tools.tools, model=...)
```

## Putting It All Together: Using Tools in an Agent

No matter how a tool is created, you make it available to an agent by passing it to the `magma.Agent` constructor. The agent's `tool_node` then handles the execution.

```python
import magma
from baml_client import b
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

# --- 1. Define State and Get a Tool ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

@magma.tool
def get_stock_price(ticker: str) -> str:
    """Retrieves the current stock price for a given ticker symbol.
    Args:
        ticker (str): The stock symbol to look up (e.g., "NVDA", "GOOG").
    """
    if ticker.upper() == "NVDA": return "125.75 USD"
    return "999.99 USD"

# --- 2. Define Prompt and Model ---
agent_prompt = magma.Prompt(baml_fn=b.MyAgent) # Assumes a BAML function exists
llm = magma.Model(id="openai/gpt-4o")

# --- 3. Define Graph Nodes ---
def agent_node(state: AgentState):
    """Calls the LLM to decide the next action."""
    response = agent_prompt(query=state['messages'][-1].content)
    return {"messages": [response]}

def tool_node(state: AgentState):
    """This node executes the tools called by the LLM."""
    tool_outputs = []
    last_message = state['messages'][-1]
    for call in last_message.tool_calls:
        tool_name = call['name']
        tool_to_call = magma.registry.tools[tool_name]
        output = tool_to_call.invoke(**call['args'])
        tool_outputs.append({"tool_call_id": call['id'], "content": str(output)})
    return {"messages": tool_outputs}

# --- 4. Build and Run Agent ---
# Make the tool available to this agent
agent = magma.Agent(
    state=AgentState,
    tools=[get_stock_price], 
    model=llm
)
# ... add nodes and edges to the agent's graph ...
# app = agent.compile()
# ... invoke app ...
```