# API Reference: `magma.prompts`

This module provides the `magma.Prompt` class, which acts as a type-safe, context-aware bridge between Python code and BAML functions.

## `magma.Prompt`

A wrapper class that makes a generated BAML function callable within the Magma ecosystem. It is designed to be executed by a `magma.Agent`, which dynamically injects the necessary model and tool configurations at runtime.

### Class Signature

```python
class Prompt:
    def __init__(self, baml_fn: Callable, name: Optional[str] = None): ...

    def invoke(self, model: "Model", tools: List["Tool"], *args: Any, **kwargs: Any) -> Any: ...
```

### Purpose

The `Prompt` class simplifies calling BAML functions from within an agent. Instead of manually managing `ClientRegistry` and `TypeBuilder` for every call, developers can instantiate a `Prompt` once. The `magma.Agent` orchestrator then uses the prompt's `invoke` method to handle the complex runtime configuration behind the scenes.

### `__init__(self, baml_fn: Callable, name: Optional[str] = None)`

*   **Parameters:**
    *   `baml_fn` (`Callable`): **Required.** A reference to the generated BAML function from your `baml_client` (e.g., `b.MyAgentFunction`).
    *   `name` (`Optional[str]`): An optional name for the prompt. If not provided, the name will be inferred from the variable it's assigned to upon registration.
*   **Behavior:**
    *   Stores the `baml_fn` for later execution.
    *   Registers itself with the `magma.registry` using the provided `name` or an inferred name.

### `invoke(self, model: "Model", tools: List["Tool"], *args: Any, **kwargs: Any) -> Any`

This is the primary method for executing the wrapped BAML function.

*   **Parameters:**
    *   `model` (`magma.Model`): **Required.** The model configuration to use for the LLM call.
    *   `tools` (`List[magma.Tool]`): **Required.** A list of tools whose schemas should be made available to the LLM.
    *   `*args`, `**kwargs`: These arguments are passed directly to the underlying BAML function.
*   **Returns:**
    *   `Any`: The return type is the Pydantic model defined as the output of the BAML function. Magma does not obscure this; you receive the fully validated, type-safe object directly from the BAML runtime.
*   **Runtime Logic:**
    *   This method is designed to be called by an orchestrator, such as `magma.Agent`.
    *   The orchestrator provides the active `magma.Model` and the list of available `magma.Tool`s as context.
    *   `invoke` uses this context to build the `baml_options` (containing the `ClientRegistry` and `TypeBuilder`) and injects them into the final BAML function call. This process is transparent to the end-user of the agent.