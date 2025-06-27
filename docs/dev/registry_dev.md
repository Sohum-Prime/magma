# API Reference: `magma.registry`

This module provides the central `Registry` class, which acts as a singleton-like object to discover and store all Magma components defined within an application's scope.

## `magma.registry` (Singleton Instance)

A globally accessible instance of the `Registry` class. This is the primary entry point for all registry interactions.

*   **Type:** `magma.registry.Registry`

## `Registry` Class

The `Registry` class is the core implementation that manages the inventory of Magma components.

### Class Signature

```python
class Registry:
    def __init__(self): ...

    @property
    def models(self) -> Dict[str, 'magma.Model']: ...

    @property
    def tools(self) -> Dict[str, 'magma.Tool']: ...

    @property
    def prompts(self) -> Dict[str, 'magma.Prompt']: ...

    def add_model(self, name: str, model: 'magma.Model') -> None: ...
    def add_tool(self, name: str, tool: 'magma.Tool') -> None: ...
    def add_prompt(self, name: str, prompt: 'magma.Prompt') -> None: ...

    def clear(self) -> None: ...
```

### Properties

#### `models`
A read-only dictionary mapping the unique name (`str`) of a model to its `magma.Model` instance.
*   **Returns:** `Dict[str, 'magma.Model']`

#### `tools`
A read-only dictionary mapping the unique name (`str`) of a tool to its `magma.Tool` instance.
*   **Returns:** `Dict[str, 'magma.Tool']`

#### `prompts`
A read-only dictionary mapping the unique name (`str`) of a prompt to its `magma.Prompt` instance.
*   **Returns:** `Dict[str, 'magma.Prompt']`

### Methods

#### `add_model(name: str, model: 'magma.Model')`
Registers a `magma.Model` instance with the registry. This method is typically called automatically from the `magma.Model` constructor.
*   **Parameters:**
    *   `name` (`str`): The unique key for the model.
    *   `model` (`magma.Model`): The model instance to register.
*   **Raises:**
    *   `ValueError`: If a model with the same `name` is already registered.

#### `add_tool(name: str, tool: 'magma.Tool')`
Registers a `magma.Tool` instance. Called automatically by the `@magma.tool` decorator or `magma.Tool` class constructor.
*   **Parameters:**
    *   `name` (`str`): The unique key for the tool (typically the function name).
    *   `tool` (`magma.Tool`): The tool instance to register.
*   **Raises:**
    *   `ValueError`: If a tool with the same `name` is already registered.

#### `add_prompt(name: str, prompt: 'magma.Prompt')`
Registers a `magma.Prompt` instance. Called automatically from the `magma.Prompt` constructor.
*   **Parameters:**
    *   `name` (`str`): The unique key for the prompt.
    *   `prompt` (`magma.Prompt`): The prompt instance to register.
*   **Raises:**
    *   `ValueError`: If a prompt with the same `name` is already registered.

#### `clear()`
Resets the registry, clearing all registered components. This is primarily intended for use in testing environments to ensure test isolation.