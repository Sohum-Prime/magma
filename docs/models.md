# Models: The Universal LLM Interface

At the core of any agent is a foundation model. Project Magma is designed to be model-agnostic, allowing you to seamlessly switch between hundreds of different LLMs from providers like OpenAI, Anthropic, Google, and Cohere, as well as open-source models running locally via Ollama or on services like Hugging Face.

This is achieved through our integration with **LiteLLM**, a brilliant library that provides a unified, standardized API for all model providers. Magma abstracts this into a clean and simple `magma.Model` class.

## Core Concept: One Class to Rule Them All

You don't need to learn different SDKs or manage complex proxy configurations. In Magma, every model is defined as an instance of the `magma.Model` class.

```python
import magma
import os

# --- Define a model for OpenAI ---
# API key is automatically picked up from the OPENAI_API_KEY environment variable.
gpt_4o = magma.Model(id="openai/gpt-4o")

# --- Define a model for Anthropic ---
# API key is picked up from ANTHROPIC_API_KEY.
claude_3_sonnet = magma.Model(id="anthropic/claude-3-5-sonnet-20240620")

# --- Define a locally running Ollama model ---
# For local models, you often need to specify the api_base.
# All keyword arguments are passed directly to LiteLLM.
local_llama3 = magma.Model(
    id="ollama/llama3",
    api_base="http://localhost:11434"
)
```

The `magma.Model` object is a lightweight configuration container. It holds all the information Magma needs to make a call through LiteLLM.

## How It Works: SDK-First, No Proxies Needed

To ensure the simplest possible developer experience, Magma is built on the **LiteLLM Python SDK**, not the LiteLLM Proxy.

*   **Why the SDK?** The SDK is a direct Python dependency. It runs in the same process as your agent, requiring zero extra setup. This means you can `pip install magma` and immediately have access to 100+ models.
*   **Why not the Proxy?** The LiteLLM Proxy is a powerful tool for platform teams who need a centralized gateway to manage keys, costs, and rate limits for an entire organization. However, it requires running a separate server process, which adds unnecessary complexity for developers building applications with a library like Magma.

When your agent needs to call an LLM, Magma performs the following steps under the hood:
1.  It takes the `magma.Model` object you've provided to the agent.
2.  It prepares the messages and tool schemas.
3.  It calls `litellm.completion()` using the parameters from your `magma.Model` object.

```python
# Conceptual view of what Magma does internally
import litellm

def execute_llm_call(model: magma.Model, messages: list, **kwargs):
    # Unpack the model's parameters and call LiteLLM
    response = litellm.completion(
        model=model.id,
        messages=messages,
        **model.params, # Pass temperature, api_base, etc.
        **kwargs      # Pass other runtime args like tools
    )
    return response
```

This design keeps the implementation transparent and leverages LiteLLM's core strength: a unified API for completions.

## Advanced Usage

### Customizing Model Parameters

You can pass any parameter supported by `litellm.completion` directly into the `magma.Model` constructor. This is useful for setting temperature, top-p, or provider-specific options.

```python
# A model with a low temperature for more deterministic outputs
creative_model = magma.Model(
    id="openai/gpt-4o",
    temperature=0.2,
    max_tokens=2048,
    response_format={"type": "json_object"} # OpenAI specific kwarg
)
```

### Using Azure OpenAI

For providers that require more configuration, like Azure, simply pass the required parameters. LiteLLM handles the rest.

```python
azure_gpt4 = magma.Model(
    # The 'model' parameter for LiteLLM's Azure integration
    # is the deployment name prefixed with 'azure/'.
    id="azure/my-gpt4o-deployment",
    # LiteLLM knows to look for these specific kwargs for Azure
    api_base=os.environ["AZURE_API_BASE"],
    api_version=os.environ["AZURE_API_VERSION"],
    api_key=os.environ["AZURE_API_KEY"]
)
```

### Runtime Model Selection

Because models are just Python objects, you can easily implement logic to select the right model for the job within your agent's graph.

```python
# In your agent's graph node
def router_node(state: AgentState):
    query = state['messages'][-1].content
    
    # Define your models
    fast_model = magma.Model(id="ollama/llama3")
    powerful_model = magma.Model(id="openai/gpt-4o")

    # Simple routing logic
    if len(query) < 100:
        # Use a fast, cheap model for simple queries
        selected_model = fast_model
    else:
        # Use a powerful model for complex queries
        selected_model = powerful_model
    
    # The agent will now use the selected model for the next LLM call
    return {"active_model": selected_model}
```

## Integration with BAML

A common question is how `magma.Model` interacts with the `client` defined inside a `.baml` file. The relationship is simple and designed for clarity:

**The `magma.Model` instance provided to the `magma.Agent` always wins.**

*   **BAML `client` as a Fallback:** The `client` you define in your BAML function (e.g., `client openai/gpt-4o`) is primarily used for testing and validation inside the BAML VSCode Playground. It ensures your `.baml` file is self-contained and testable.
*   **Magma Override at Runtime:** When you execute a `magma.Prompt`, Magma's orchestrator uses the `magma.Model` object from your agent's configuration. It dynamically constructs a BAML `ClientRegistry` on the fly and passes it into the BAML function call, overriding the default `client`.

This separation of concerns allows you to:
1.  Test your prompts in isolation using the BAML playground.
2.  Manage all production model logic and configuration explicitly in your Python code, where it belongs.