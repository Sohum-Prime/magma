# The Magma Registry: Your Agent's Automatic Inventory

In any complex system, knowing what components you have available is crucial. When building an agent with multiple models, tools, and prompts, you need an easy way to see and access everything you've defined.

The **Magma Registry** is the central nervous system of your application. It's a simple, globally accessible object that automatically keeps an inventory of every Magma component you create.

## Core Concept: Zero-Boilerplate Registration

The best part about the registry is that you don't have to do anything to use it. It works automatically.

When you define a Magma component, it registers itself with the `magma.registry` behind the scenes.

*   Create a `magma.Model`? It's in the registry.
*   Decorate a function with `@magma.tool`? It's in the registry.
*   Define a `magma.Prompt`? It's in the registry.

This eliminates the need for manual bookkeeping, like appending components to lists or managing complex configuration objects. Your code stays clean, and you always have a single source of truth for all the building blocks of your agent.

## How to Use It: Inspecting Your Components

The primary way you'll interact with the registry is by inspecting its contents to see what's available. This is incredibly useful during development and debugging.

The registry is accessed via the top-level `magma` import. Its components are stored in dictionary-like objects:

*   `magma.registry.models`
*   `magma.registry.tools`
*   `magma.registry.prompts`

### Example

Imagine you're setting up your agent in a Python script or a Jupyter notebook. You can easily get a sense of your declared components:

**`main.py`**
```python
import magma
import os

# --- 1. Define your components as usual ---

# Define some models
gpt4o = magma.Model(id="openai/gpt-4o", name="gpt4o")
claude_sonnet = magma.Model(id="anthropic/claude-3-5-sonnet-20240620", name="claude_sonnet")

# Define a tool
@magma.tool
def get_weather(city: str) -> str:
    """Gets the current weather for a specified city."""
    # ... implementation ...
    return f"The weather in {city} is sunny."

# --- 2. Inspect the registry ---

print("--- Magma Component Registry ---")

# See all registered models by the name you provided
print("\nAvailable Models:")
print(magma.registry.models)
# Expected Output:
# {'gpt4o': <magma.Model id='openai/gpt-4o'>, 'claude_sonnet': <magma.Model id='anthropic/claude-3-5-sonnet-20240620'>}

# See all registered tools by their function name
print("\nAvailable Tools:")
print(magma.registry.tools)
# Expected Output:
# {'get_weather': <magma.Tool name='get_weather'>}

# You can access a specific component by its key
print(f"\nDetails for 'gpt4o' model: {magma.registry.models['gpt4o']}")
```

> **Note on Naming:**
> For `magma.Model`, you provide an explicit `name` to act as the key in the registry. For `@magma.tool` and `magma.Prompt`, the key is automatically the name of the decorated function or the variable you assign it to.

## Use in Practice: Wiring Your Agent

The registry isn't just for inspection—it's a crucial part of wiring your agent together. For example, a tool executor node in your agent graph needs to find and call the correct tool based on the LLM's output. The registry makes this trivial.

```python
# Conceptual tool executor node
def tool_node(state: AgentState):
    tool_calls = state['messages'][-1].tool_calls
    
    for call in tool_calls:
        # The LLM gives us the tool name as a string
        tool_name = call.__class__.__name__
        
        # The registry lets us easily look up the callable tool object
        if tool_name in magma.registry.tools:
            tool_to_call = magma.registry.tools[tool_name]
            # ... invoke the tool ...
        else:
            # ... handle case where tool doesn't exist ...
```

This pattern of "look up by name" makes your agent's logic clean and decouples the graph definition from the tool implementation.

## What's Registered?

In `v0.1`, the Magma registry will automatically track the following components:

*   **Models:** Every instance of `magma.Model`.
*   **Tools:** Every function decorated with `@magma.tool` or class that inherits from `magma.Tool`.
*   **Prompts:** Every instance of `magma.Prompt`.

As Magma evolves, any new core components will also be integrated into the registry, maintaining it as the central, discoverable inventory for your entire agentic system.