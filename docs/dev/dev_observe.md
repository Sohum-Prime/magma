# API Reference: `magma.observe`

This module provides tracing and observability capabilities for the Magma framework by integrating with LangFuse. The primary goal is to offer automatic, zero-effort tracing for all agent operations, with a simple decorator for extending tracing to custom functions.

## `@magma.trace` Decorator

A decorator that wraps a function to trace its execution as a span in LangFuse. This is a direct alias for `langfuse.observe` and is the recommended way to trace custom business logic within your agent.

### Decorator Signature
```python
from langfuse import observe as trace
```

### Purpose
Use `@magma.trace` to gain visibility into any Python function's execution within the context of a larger agent run. It automatically captures the function's name, inputs, outputs, execution time, and any exceptions raised.

### Usage
```python
from magma.observe import trace

@trace(name="custom-data-validation")
def validate_user_profile(profile: dict) -> bool:
    # This function's execution will appear as a 'custom-data-validation'
    # span in the LangFuse UI.
    return "email" in profile

# In a graph node:
def some_node(state: AgentState):
    is_valid = validate_user_profile(state["profile"])
    # ...
```

All parameters available to `langfuse.observe` (e.g., `name`, `as_type`) can be used with `@magma.trace`.

## Automatic Tracing (Internal Mechanism)

Magma is designed to provide comprehensive tracing automatically. This behavior is configured and enabled by the `magma.Agent` class and does not require manual setup beyond setting environment variables.

### Initialization

*   When a `magma.Agent` is instantiated, it checks for the presence of `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` environment variables.
*   If found, it initializes a global `Langfuse()` client instance.

### Core Integrations

1.  **LangGraph Tracing:**
    *   During the `agent.compile()` step, a `LangfuseCallbackHandler` is automatically injected into the LangGraph application's configuration.
    *   This handler creates a parent span for each node execution (e.g., `agent_node`, `tool_node`), ensuring the graph's flow is clearly represented in the trace.

2.  **LiteLLM Tracing (for `magma.Model` calls):**
    *   Upon initialization, the `magma.Agent` sets the global LiteLLM callbacks:
        ```python
        import litellm
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
        ```
    *   Because all `magma.Model` calls are executed via `litellm.completion`, every LLM call is automatically captured as a "generation" in LangFuse. This includes the model name, prompt, response, token usage, and cost.

3.  **BAML and Tool Tracing:**
    *   Calls to `magma.Prompt` (which trigger BAML functions) and `@magma.tool` functions occur *within* a graph node.
    *   Since the node itself is already traced by the `LangfuseCallbackHandler`, and the subsequent LLM call is traced by the LiteLLM callback, these operations appear as perfectly nested child spans within the overall trace without any extra effort.

This multi-layered, automatic approach ensures that a single agent run produces a rich, hierarchical trace that is immediately useful for debugging and analysis.