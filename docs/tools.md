# Tools: Empowering Agents with Capabilities

An agent is only as capable as the tools it can wield. Tools are the bridge between the LLM's reasoning abilities and the outside world, allowing it to fetch information, execute code, or interact with any API.

Magma, inspired by the developer-friendly approach of **smolagents**, makes defining tools incredibly simple and robust. You can turn any Python function into a secure, type-safe tool that your agent can reliably use, simply by adding a decorator.

## Core Concept: The `@magma.tool` Decorator

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

For the decorator to work effectively, your function should have:
1.  **A clear name** (`get_stock_price`). This becomes the tool's identifier.
2.  **Type-hinted parameters** (`ticker: str`). This allows Magma to generate a precise schema.
3.  **A descriptive docstring**. The LLM uses this description to understand *what the tool does* and *when to use it*. The `Args` section is crucial for explaining the parameters.

## How It Works: The Magic Behind the Decorator

When you apply the `@magma.tool` decorator, Magma performs a powerful "dual-creation" process behind the scenes to bridge the gap between your Python code and the BAML-powered LLM interaction:

1.  **Introspection:** The decorator inspects your Python function's signature, type hints, and docstring.
2.  **Execution Object:** It creates a `smolagents.Tool`-compatible object in memory. This object holds the actual Python code to be **executed** by the agent when the tool is called.
3.  **Schema Generation:** Simultaneously, it generates a BAML `class` definition as a string. For the example above, it would generate:
    ```baml
    // Description is automatically extracted from the docstring.
    class get_stock_price @description("Retrieves the current stock price...") {
      ticker string @description("The stock symbol to look up...")
      currency string @description("The currency to return the price in...")
    }
    ```
4.  **Runtime Injection:** When a `magma.Prompt` is executed, the `magma.Agent` gathers all registered tool schemas and uses BAML's **`TypeBuilder`** to inject them into the prompt. This makes the LLM aware of the exact tools and arguments available for that specific call, ensuring a type-safe and reliable function call.

This process gives you the best of both worlds: the simplicity of writing a Python function and the robustness of a schema-defined LLM interface.

## Using Tools in an Agent

To make tools available to an agent, you simply pass them to the `magma.Agent` constructor. The agent's `tool_node` then handles the execution.

```python
import magma
from baml_client import b
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

# --- 1. Define State and Tool ---
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

@magma.tool
def get_stock_price(ticker: str) -> float:
    """Retrieves the current stock price for a given ticker symbol."""
    if ticker.upper() == "NVDA": return 125.75
    return 999.99

# --- 2. Define Prompt and Model ---
agent_prompt = magma.Prompt(baml_fn=b.MyAgent) # Assumes a BAML function exists
llm = magma.Model(id="openai/gpt-4o")

# --- 3. Define Graph Nodes ---
def agent_node(state: AgentState):
    """Calls the LLM to decide the next action."""
    response = agent_prompt(query=state['messages'][0].content)
    return {"messages": [response]}

def tool_node(state: AgentState):
    """This node executes the tools called by the LLM."""
    tool_calls = state['messages'][-1].tool_calls
    tool_outputs = []
    for call in tool_calls:
        # Magma's registry finds and invokes the correct tool by name.
        tool_name = call.__class__.__name__
        tool_to_call = magma.registry.tools[tool_name]
        output = tool_to_call.invoke(call.model_dump())
        tool_outputs.append({"tool_call_id": call.id, "content": str(output)})
    return {"messages": tool_outputs}

# --- 4. Build and Run Agent ---
agent = magma.Agent(
    state=AgentState,
    tools=[get_stock_price], # Make the tool available to this agent
    model=llm
)
# ... add nodes and edges ...
app = agent.compile()
# ... invoke app ...
```

## Advanced Usage

### Complex Tools with State (`magma.Tool` Class)

For tools that require shared state, initialization logic, or multiple methods, you can subclass `magma.Tool` directly. This pattern is useful for things like database connections or API clients.

```python
import magma

class DatabaseTool(magma.Tool):
    name = "sql_executor"
    description = "Executes a SQL query against the company database."
    
    def __init__(self, connection_string: str):
        # Expensive setup can happen here
        self.connection = self._connect_to_db(connection_string)

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

# Instantiate your custom tool class
db_tool = DatabaseTool(connection_string=os.environ["DB_URL"])

# Register it with the agent
agent = magma.Agent(state=..., tools=[db_tool], model=...)
```
Magma will introspect your `invoke` method to generate the BAML schema, just as it does for a decorated function.

### Leveraging Pre-Built Tools & Collections

You don't have to build every tool from scratch. Magma provides wrappers to easily import tools from other popular ecosystems.

#### LangChain Tools

Easily convert a tool from the extensive LangChain ecosystem.

```python
from langchain.agents import load_tools as load_lc_tools

# Load a LangChain tool
lc_search_tool = load_lc_tools(["serpapi"])[0]

# Wrap it for Magma
search_tool = magma.Tool.from_langchain(lc_search_tool)

# Use it in your agent
agent = magma.Agent(state=..., tools=[search_tool], model=...)
```

#### Smolagents Tool Collections

You can load entire collections of tools from the Hugging Face Hub.

```python
from smolagents import ToolCollection

# Load a curated collection of diffusion tools
image_tools_collection = ToolCollection.from_hub(
    "huggingface-tools/diffusion-tools-6630bb19a942c2306a2cdb6f"
)

# The tools attribute is a list of tool objects
agent = magma.Agent(state=..., tools=[*image_tools_collection.tools], model=...)
```

No matter how a tool is created—with the decorator, a custom class, or from another library—it becomes a standardized `magma.Tool` object. Once you pass it to the `magma.Agent`, the BAML schema generation and runtime execution work automatically.