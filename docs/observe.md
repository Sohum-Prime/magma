# Observability: Tracing Your Agent's Every Move

Building an agent can feel like working with a black box. Why did it choose that tool? What was the exact prompt it used? How much did that call cost? Answering these questions is fundamental to debugging, improving, and running agents in production.

Magma provides first-class observability out-of-the-box by integrating with **LangFuse**, the open-source LLM engineering platform. Every action your agent takes is automatically captured, traced, and visualized, giving you a complete, end-to-end view of its execution.

## Core Concept: Automatic, Deep Tracing

You don't need to manually instrument every function call. When you run a `magma.Agent`, the framework automatically traces:
*   **The Overall Run:** The entire `app.invoke()` or `app.stream()` call is captured as a single parent trace.
*   **Graph Structure:** Each node execution in your LangGraph-powered agent appears as a nested span, showing you the flow of control.
*   **LLM Calls:** Every call made through a `magma.Prompt` is captured as a "generation" span, including the final rendered prompt, model parameters, latency, token usage, and cost.
*   **Tool Calls:** Every time a `@magma.tool` is executed, it appears as a span with its inputs and outputs.

This creates a rich, hierarchical trace in the LangFuse UI that lets you drill down from a high-level agent run into the specifics of a single LLM call or tool execution.

### Setup: Just Add Environment Variables

To enable observability, you don't need to change a single line of your agent's code. Simply set the following environment variables before running your application:

```bash
# Get these from your Langfuse project settings
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="https://cloud.langfuse.com" # Or your self-hosted URL
```

Once these are set, the `magma.Agent` will automatically detect them and configure the LangFuse handler. All subsequent runs will be sent to your LangFuse project.

## How It Works: Seamless Integration

Magma's `Agent` class acts as the central point for configuring tracing, ensuring all components work together to produce a single, unified trace.

1.  **Agent Initialization:** When you create a `magma.Agent`, it checks for the LangFuse environment variables. If found, it initializes the LangFuse Python SDK.
2.  **LangGraph Callback:** It automatically adds the `LangfuseCallbackHandler` to the LangGraph `app` when you call `agent.compile()`. This handler is responsible for tracing all node and edge executions within the graph.
3.  **LiteLLM Integration:** It configures a global LiteLLM callback to LangFuse. Because all `magma.Model` calls go through LiteLLM, every LLM interaction is automatically captured. This integration is crucial as it's where detailed information like token counts and costs are recorded.
4.  **BAML and Tool Tracing:** Calls to `magma.Prompt` and `@magma.tool` functions happen *inside* a graph node. Because the node execution is already being traced by the LangGraph handler, these operations appear as nested spans within the trace, providing a clear and logical hierarchy.

## Tracing Custom Functions with `@magma.trace`

Sometimes you have important business logic that isn't a graph node or a tool, but you still want to see it in your traces. For this, Magma provides the `@magma.trace` decorator, which is a simple alias for LangFuse's powerful `@observe` decorator.

```python
import magma

@magma.trace(name="data-cleaning-logic")
def clean_user_input(query: str) -> str:
    """A custom function to pre-process user input."""
    # ... your logic here ...
    cleaned_query = query.strip().lower()
    return cleaned_query

# Now, if you call this function from within a graph node...
def agent_node(state: AgentState):
    query = state['messages'][0].content
    cleaned_query = clean_user_input(query=query)
    # ...
```

In the LangFuse UI, you will see a "data-cleaning-logic" span nested inside your "agent_node" span, complete with its inputs and outputs.

## Adding Richer Context

LangFuse allows you to add rich context to your traces, which is incredibly useful for filtering and analysis. Magma exposes this functionality directly.

### Tracking Users

You can associate a trace with a specific user ID. This is invaluable for debugging user-reported issues.

```python
# In your agent invocation
app = agent.compile()
app.invoke(
    {"messages": [("user", "some query")]},
    config={
        "configurable": {
            # This user_id will be attached to the trace in Langfuse
            "user_id": "user-12345"
        }
    }
)
```

### Adding Metadata and Tags

You can add arbitrary metadata or simple tags to any trace or span to make it easier to find later.

```python
from langfuse import Langfuse

langfuse = Langfuse() # Magma initializes this automatically, but you can get the instance

@magma.trace()
def my_function(state):
    # Add metadata to the current span
    langfuse.get_current_observation().update(
        metadata={"customer_tier": "enterprise"}
    )
    
    # Add a tag to the parent trace
    langfuse.get_current_trace().update(tags=["alpha-feature", "critical-path"])
    
    # ... function logic ...
```

By combining automatic tracing with these simple tools for adding custom context, Magma and LangFuse provide a complete observability solution for building, debugging, and monitoring production-grade AI agents.