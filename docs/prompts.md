# Prompts: Type-Safe Communication with LLMs

The most critical—and often most brittle—part of an AI agent is its communication with the Large Language Model. Traditional methods rely on f-string formatting and manually parsing JSON, which is error-prone and hard to maintain.

Magma solves this by integrating **BAML**, a domain-specific language designed specifically for defining reliable, type-safe interactions with LLMs. Instead of manipulating strings in Python, you define the *structure* of your prompt in a `.baml` file and call it like a regular function.

## Core Concept: Separating Prompt Logic from Application Logic

With Magma, your LLM interaction is split into two clear parts:

1.  **The BAML File (`.baml`):** This is where you do your prompt engineering. You define the expected input/output schemas (`class`), the prompt template, and a default model for testing. This file is your single source of truth for *what* the LLM should do.
2.  **The Python Code (`.py`):** This is where you orchestrate *when* and *how* to call the LLM. You use the `magma.Prompt` class to create a callable Python object that represents your BAML function.

This separation makes your prompts reusable, testable in isolation (using the BAML VSCode extension), and far easier to manage than scattered string templates.

### The `magma.Prompt` Class

The `magma.Prompt` class is the bridge between your Python code and your BAML functions. You instantiate it by passing a function from your generated `baml_client`.

**`./baml_src/prompts.baml`**
```baml
class ExtractedInfo {
  name string
  email string
}

function ExtractUser(text: string) -> ExtractedInfo {
  client openai/gpt-4o-mini
  prompt #"
    Extract the user's name and email from the following text:
    ---
    {{ text }}
    ---
    {{ ctx.output_format }}
  "#
}
```

After running `baml-cli generate`, you can create a `magma.Prompt` object in Python:

**`main.py`**
```python
import magma
from baml_client import b # Your generated BAML client

# Create a callable prompt object linked to the BAML function.
extract_user_prompt = magma.Prompt(baml_fn=b.ExtractUser)

# Now you can use this in your agent logic.
# The result will be a type-safe Pydantic object matching the 'ExtractedInfo' class.
# result = extract_user_prompt(text="My name is Jane Doe and my email is jane@example.com")
```

## How It Works: Dynamic Power at Runtime

The real power of the `magma.Prompt` integration comes from its ability to dynamically configure the BAML runtime based on your agent's context.

When you call a `magma.Prompt` object from within a `magma.Agent` graph, Magma automatically performs these steps:

1.  **Gathers Context:** It looks at the agent's current configuration to identify the active `magma.Model` and the list of available `magma.Tool`s.
2.  **Builds a Client Registry:** It creates a BAML `ClientRegistry` on the fly, telling BAML to use the `magma.Model` you've specified for this specific call. This overrides the default `client` in the `.baml` file.
3.  **Builds a Type Builder:** It iterates through all the `magma.Tool`s available to the agent. For each tool, it generates the corresponding BAML `class` definition and uses a `TypeBuilder` to inject these classes into your prompt's schema. This is how the LLM becomes aware of the tools it can use.
4.  **Executes the Call:** It invokes the underlying BAML function with these dynamically generated `baml_options`, ensuring the LLM receives a prompt that is perfectly tailored to the agent's current capabilities and configuration.

### Example: A Tool-Using Agent

This pattern is what enables dynamic tool use in a clean, maintainable way.

**`./baml_src/agent.baml`**
```baml
// Define a placeholder union for our tools.
// The `@@dynamic` attribute tells BAML that Magma will add to this at runtime.
type Toolbox @@dynamic

class AgentResponse {
  // The LLM can choose to call one or more tools from the dynamic Toolbox.
  tool_calls Toolbox[]?
  final_answer string?
}

function MyAgent(query: string) -> AgentResponse {
  client openai/gpt-4o
  prompt #"
    You are a helpful assistant. You have access to a set of tools.
    User query: {{ query }}

    Based on the query, decide which tool to use from the following options.
    {{ ctx.output_format }}
  "#
}
```

**`main.py`**
```python
import magma
from baml_client import b

# Define a tool in Python
@magma.tool
def get_stock_price(ticker: str) -> float:
    """Retrieves the current stock price for a given ticker symbol."""
    # ... implementation ...
    return 150.75

# Create the prompt object
agent_prompt = magma.Prompt(baml_fn=b.MyAgent)

# Define the agent, making the tool available
agent = magma.Agent(
    state=...,
    tools=[get_stock_price], # Make the tool available to this agent
    model=magma.Model(id="openai/gpt-4o")
)

# Inside a node, when you call the prompt...
# response = agent_prompt(query="What is the price of NVDA?")
#
# ...Magma will automatically:
# 1. Use the "openai/gpt-4o" model.
# 2. Generate a 'class get_stock_price { ticker string }' BAML definition.
# 3. Add 'get_stock_price' to the 'Toolbox' union.
# 4. Send the complete schema to the LLM.
# 5. Parse the response into a type-safe 'AgentResponse' object,
#    which may contain a 'get_stock_price' instance.
```

This architecture gives you the ultimate combination of structure and flexibility. You define the stable parts of your prompt in BAML and let Magma handle the dynamic, context-dependent parts in Python.