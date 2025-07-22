# API Reference: `magma.models`

This module provides the core `Model` class, which serves as a universal configuration wrapper for any Large Language Model (LLM) supported by LiteLLM.

## `magma.Model`

A configuration class that defines a specific LLM and its parameters. Magma uses these objects to make calls via the LiteLLM SDK and to configure the BAML runtime for type-safe prompting.

### Class Signature

```python
class Model:
    def __init__(self, id: str, **kwargs: Any):
        ...
```

### Purpose

The `Model` class is designed to be a simple, immutable container for all the information needed to call an LLM. It decouples model configuration from the agent's execution logic, allowing for easy runtime model switching and clear, explicit setup.

### Attributes

*   **`id`** (`str`): **Required.** The unique identifier for the model in LiteLLM format. This string dictates which provider and model to use.
    *   **Examples:** `"openai/gpt-4o"`, `"anthropic/claude-3-5-sonnet-20240620"`, `"ollama/llama3"`, `"azure/my-deployment-name"`.
*   **`params`** (`Dict[str, Any]`): A dictionary containing all other keyword arguments passed to the constructor. These are passed directly to `litellm.completion`, allowing for customization of parameters like `temperature`, `max_tokens`, `api_base`, `api_key`, etc.

### Methods

#### `to_baml_client() -> baml_py.ClientRegistry`

This is the key integration method used internally by Magma to bridge the gap with BAML. It translates the `magma.Model` configuration into a BAML `ClientRegistry` object. This allows Magma to dynamically override the `client` specified in a `.baml` file at runtime, ensuring the agent uses the exact model defined in your Python code.

*   **Returns:** A `baml_py.ClientRegistry` instance configured with a single client named `"magma-client"` that is set as the primary client.
*   **Behavior:**
    *   It parses the `provider` from the `id` string (e.g., `"openai/gpt-4o"` -> provider `"openai"`).
    *   It passes the model name and all items in `self.params` as `options` to the BAML client.