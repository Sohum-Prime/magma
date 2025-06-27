# API Reference: `magma.prompts`

This module provides the `magma.Prompt` class, which acts as a type-safe, context-aware bridge between Python code and BAML functions.

## `magma.Prompt`

A wrapper class that makes a generated BAML function callable within the Magma ecosystem. It automatically handles the dynamic injection of models and tools at runtime.

### Class Signature

```python
class Prompt:
    def __init__(self, baml_fn: Callable, name: Optional[str] = None): ...

    def __call__(self, *args, **kwargs) -> Any: ...
```

### Purpose

The `Prompt` class simplifies calling BAML functions from within an agent. Instead of manually managing `ClientRegistry` and `TypeBuilder` for every call, developers can instantiate a `Prompt` once and call it like a regular Python function. The Magma orchestrator handles the complex runtime configuration behind the scenes.

### `__init__(self, baml_fn: Callable, name: Optional[str] = None)`

*   **Parameters:**
    *   `baml_fn` (`Callable`): **Required.** A reference to the generated BAML function from your `baml_client` (e.g., `b.MyAgentFunction`).
    *   `name` (`Optional[str]`): An optional name for the prompt. If not provided, the name will be inferred from the variable it's assigned to upon registration.
*   **Behavior:**
    *   Stores the `baml_fn` for later execution.
    *   Registers itself with the `magma.registry` using the provided `name` or an inferred name.

### `__call__(self, *args, **kwargs) -> Any`

This makes instances of the `Prompt` class callable.

*   **Parameters:**
    *   `*args`, `**kwargs`: These arguments are passed directly to the underlying BAML function.
*   **Returns:**
    *   `Any`: The return type is the Pydantic model defined as the output of the BAML function. Magma does not obscure this; you receive the fully validated, type-safe object directly from the BAML runtime.
*   **Runtime Magic:**
    *   **This method should not be called directly in most cases.** It is a placeholder for a more complex internal execution flow. When invoked from within a `magma.Agent` run, the agent's orchestrator intercepts the call.
    *   The orchestrator provides the active `magma.Model` and the list of available `magma.Tool`s as context.
    *   It uses this context to build the `baml_options` (containing the `ClientRegistry` and `TypeBuilder`) and injects them into the final BAML function call. This process is transparent to the user.