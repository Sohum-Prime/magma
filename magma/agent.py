import os
from typing import Any, Callable, Dict, List, Optional, Type, TypedDict
from functools import wraps

# LangGraph is a core dependency
from langgraph.graph import StateGraph, END

# Import other Magma components
from .models import Model
from .tools import Tool
from .prompts import Prompt

# Optional dependencies for observability
try:
    import litellm
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler
    LANGFUSE_INSTALLED = True
except ImportError:
    LANGFUSE_INSTALLED = False

class Agent:
    """
    The primary orchestrator for building, configuring, and running
    stateful, graph-based agentic workflows.
    """
    def __init__(
        self,
        state: Type[TypedDict],
        model: Model,
        tools: Optional[List[Tool]] = None,
    ):
        """
        Initializes the agent graph builder.

        Args:
            state: A TypedDict class defining the agent's state.
            model: The default magma.Model to use for prompts in this agent.
            tools: A list of magma.Tool instances available to this agent.
        """
        self.state = state
        self.model = model
        self.tools = tools or []
        self._graph = StateGraph(state)
        self._langfuse_handler = None

        self._setup_observability()

    def _setup_observability(self):
        """Initializes LangFuse and LiteLLM callbacks if configured."""
        if LANGFUSE_INSTALLED and os.getenv("LANGFUSE_PUBLIC_KEY"):
            print("Magma: LangFuse credentials detected. Enabling observability.")
            self._langfuse_handler = CallbackHandler()
            
            # Configure LiteLLM to send traces to LangFuse
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]
        else:
            # Ensure callbacks are not set if LangFuse is not configured
            litellm.success_callback = []
            litellm.failure_callback = []

    def _get_node_wrapper(self, node_func: Callable) -> Callable:
        """Wraps a node function to manage the prompt execution context."""
        @wraps(node_func)
        def context_wrapper(state: TypedDict) -> Dict[str, Any]:
            # Set the context for any magma.Prompt calls inside the node
            Prompt._agent_context = {
                "model": self.model,
                "tools": self.tools,
            }
            try:
                # Execute the original node function
                result = node_func(state)
                return result
            finally:
                # Always clear the context after the node finishes
                Prompt._agent_context = None
        return context_wrapper

    def add_node(self, name: str, node_func: Callable) -> None:
        """Adds a function as a node to the agent's graph."""
        wrapped_node = self._get_node_wrapper(node_func)
        self._graph.add_node(name, wrapped_node)

    def add_edge(self, start_key: str, end_key: str) -> None:
        """Adds a direct edge between two nodes."""
        self._graph.add_edge(start_key, end_key)

    def add_conditional_edges(
        self,
        start_key: str,
        condition: Callable,
        path_map: Optional[Dict[str, str]] = None,
    ) -> None:
        """Adds conditional edges from a node to others."""
        self._graph.add_conditional_edges(start_key, condition, path_map)

    def set_entry_point(self, key: str) -> None:
        """Sets the starting node for the graph."""
        self._graph.set_entry_point(key)

    def compile(self, checkpointer: Optional[Any] = None) -> Any:
        """
        Finalizes the graph and returns a runnable LangGraph application.

        Args:
            checkpointer: An optional LangGraph checkpointer for persistence.

        Returns:
            A compiled LangGraph application.
        """
        callbacks = []
        if self._langfuse_handler:
            callbacks.append(self._langfuse_handler)

        return self._graph.compile(checkpointer=checkpointer, callbacks=callbacks)