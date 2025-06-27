# API Reference: `magma.tools`

This module provides the `Tool` class and the `@tool` decorator, which are the primary mechanisms for defining agent capabilities. The key responsibility of this module is to create a standardized tool interface that can be both executed by the agent and automatically translated into a BAML schema for the LLM.

## `@magma.tool` Decorator

A decorator that transforms a standard Python function into a `magma.Tool` instance, automatically registering it and making it available to the agent framework.

### Decorator Signature
```python
def tool(func: Callable) -> 'Tool': ...
```

### Purpose
This is the simplest and most common way to create a tool. It promotes a clean, Pythonic style where a tool is just a function with a docstring and type hints.

### Behavior
1.  **Introspection:** The decorator inspects the wrapped function's `__name__`, `__doc__`, and `__annotations__` to extract its name, description, parameters, and type hints.
2.  **Registration:** It automatically registers the created `Tool` instance with the `magma.registry` using the function's name as the key.
3.  **Schema Generation:** It uses the introspected information to generate a BAML `class` schema string, which is used by `magma.Prompt` at runtime.

### Requirements for Decorated Functions
*   Must have a descriptive docstring. The first line is used as the tool's main description.
*   Must include an `Args:` section in the docstring to describe each parameter for the LLM.
*   All arguments must have type hints (e.g., `ticker: str`).

## `Tool` Class

The base class for all tools in Magma. It can be subclassed to create more complex, stateful tools.

### Class Signature
```python
class Tool:
    def __init__(self, name: str, description: str, func: Callable): ...
    def invoke(self, *args, **kwargs) -> Any: ...
    def to_baml_schema(self) -> str: ...

    @classmethod
    def from_langchain(cls, lc_tool: Any) -> 'Tool': ...
```

### Methods

#### `invoke(*args, **kwargs) -> Any`
Executes the tool's underlying function. This is called by the agent's tool-executing node.
*   **Returns:** The result of the wrapped function.

#### `to_baml_schema() -> str`
**This is the core integration point with the prompt system.** It generates a BAML `class` definition as a string based on the tool's name, description, and parameters.
*   **Returns:** A string containing a valid BAML class definition. E.g., `class my_tool @description("...") { arg1: string; }`

### Class Methods

#### `from_langchain(lc_tool: Any) -> 'Tool'`
A class method to create a `magma.Tool` instance from an existing LangChain tool object.
*   **Parameters:**
    *   `lc_tool` (`langchain_core.tools.BaseTool`): An instance of a LangChain tool.
*   **Returns:** A new `magma.Tool` instance.
*   **Behavior:** It extracts the `name`, `description`, and argument schema (`args_schema`) from the LangChain tool and uses them to construct a compatible `magma.Tool`.