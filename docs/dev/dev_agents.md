# API Reference: `magma.agent`

This module provides the `Agent` class, the primary orchestrator for building, configuring, and running agentic workflows. It serves as a developer-friendly facade over LangGraph's `StateGraph`, automatically wiring together Magma's components.

## `magma.Agent`

A class for constructing a stateful, graph-based agent.

### Class Signature
```python
class Agent:
    def __init__(
        self,
        state: Type[TypedDict],
        model: 'Model',
        tools: Optional[List['Tool']] = None,
    ): ...

    def add_node(self, name: str, node_func: Callable) -> None: ...
    def add_edge(self, start_key: str, end_key: str) -> None: ...
    def add_conditional_edges(self, start_key: str, condition: Callable, path_map: Optional[Dict[str, str]] = None) -> None: ...
    def set_entry_point(self, key: str) -> None: ...
    def compile(self, checkpointer: Optional[Any] = None) -> 'CompiledGraph': ...
```

### `__init__`
Initializes the agent graph builder.

*   **Parameters:**
    *   `state` (`Type[TypedDict]`): **Required.** A `TypedDict` class defining the structure of the agent's state.
    *   `model` (`magma.Model`): **Required.** The default `magma.Model` instance to be used for all `magma.Prompt` calls within this agent.
    *   `tools` (`Optional[List['Tool']]`): A list of `magma.Tool` instances that are available to this agent. These tools will be automatically injected into the BAML schema during prompt execution.
*   **Behavior:**
    *   Creates an internal `langgraph.StateGraph` instance with the provided `state` schema.
    *   Stores the `model` and `tools` to define the agent's execution context.
    *   **Automatic Observability Setup:** Checks for `LANGFUSE_*` environment variables. If present, it initializes the global LangFuse client and configures LiteLLM's `success_callback` and `failure_callback` to point to LangFuse. This enables automatic tracing for all LLM calls made by this agent.

### Graph Construction Methods
These methods are direct passthroughs to the internal `StateGraph` instance, providing a familiar API for developers who know LangGraph.

#### `add_node(name: str, node_func: Callable)`
Adds a function as a node to the graph.
*   **Internal Behavior:** Before adding the node, Magma wraps `node_func` to manage the agent's context. This wrapper sets `Prompt._agent_context` before the node runs and clears it after, ensuring that any `magma.Prompt` called inside the node has access to the correct model and tools.

#### `add_edge(start_key: str, end_key: str)`
Adds a direct transition from one node to another.

#### `add_conditional_edges(...)`
Adds a conditional transition, routing to different nodes based on the output of the `condition` function.

#### `set_entry_point(key: str)`
Defines the starting node of the graph.

### `compile(checkpointer: Optional[Any] = None)`
Finalizes the graph and returns a runnable application.

*   **Parameters:**
    *   `checkpointer` (`Optional[BaseCheckpointSaver]`): An optional LangGraph checkpointer for enabling persistence and memory.
*   **Returns:** A compiled LangGraph application (`langgraph.graph.CompiledGraph`).
*   **Behavior:**
    *   **Injects Observability:** If LangFuse is enabled, it automatically adds the `LangfuseCallbackHandler` to the list of callbacks passed to the underlying `graph.compile()` method.
    *   Returns the final, executable graph object, which has `.invoke()`, `.stream()`, and `.get_graph()` methods.