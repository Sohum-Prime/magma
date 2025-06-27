import inspect
from typing import Callable, Optional, Any, List

# Import dependencies that will be mocked in tests
try:
    from magma.registry import registry
    from magma.models import Model
    from magma.tools import Tool
    from baml_client import TypeBuilder
    from baml_py import ClientRegistry
except ImportError:
    # Define dummy classes for type hinting if dependencies are not available
    class Model: pass
    class Tool: pass
    class ClientRegistry: pass
    class TypeBuilder: pass
    class DummyRegistry:
        def add_prompt(self, name, prompt): pass
    registry = DummyRegistry()


class Prompt:
    """
    A type-safe, context-aware bridge between Python code and BAML functions.
    This class wraps a generated BAML function to be used within the Magma
    agent ecosystem.
    """
    _agent_context = None # Class-level context managed by the Agent orchestrator

    def __init__(self, baml_fn: Callable, name: Optional[str] = None):
        """
        Initializes the Prompt wrapper.

        Args:
            baml_fn (Callable): A reference to a generated BAML function
                               (e.g., b.MyAgentFunction).
            name (Optional[str]): A unique name for the prompt. If not provided,
                                  it will be inferred from the variable name upon
                                  first use (requires Python 3.8+).
        """
        if not callable(baml_fn):
            raise TypeError("baml_fn must be a callable BAML function.")
            
        self.baml_fn = baml_fn
        self.name = name
        
        # The name might be None initially. The registry logic could be
        # enhanced to infer it, but for v0.1 we'll rely on it being set.
        if self.name:
            registry.add_prompt(self.name, self)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Executes the BAML function with context provided by the active agent.

        Raises:
            RuntimeError: If called outside of an active magma.Agent execution context.
        
        Returns:
            The Pydantic model returned by the BAML function.
        """
        if Prompt._agent_context is None:
            raise RuntimeError(
                "A magma.Prompt must be called from within an active magma.Agent execution context. "
                "The context provides the necessary model and tool configurations."
            )
        
        model = Prompt._agent_context.get("model")
        tools = Prompt._agent_context.get("tools", [])

        if not isinstance(model, Model):
             raise TypeError("Agent context is missing a valid magma.Model instance.")

        return self._execute_with_context(model, tools, *args, **kwargs)

    def _execute_with_context(
        self, model: "Model", tools: List["Tool"], *args: Any, **kwargs: Any
    ) -> Any:
        """Internal method to run BAML function with dynamic options."""
        
        # 1. Create BAML client registry from the agent's model
        client_registry = model.to_baml_client()

        # 2. Create BAML type builder from the agent's tools
        type_builder = TypeBuilder()
        for tool in tools:
            # Assumes tool object has a method to provide its BAML schema string
            if hasattr(tool, 'to_baml_schema'):
                type_builder.add_baml(tool.to_baml_schema())

        # 3. Prepare baml_options to be passed to the BAML function
        baml_options = {
            "client_registry": client_registry,
            "tb": type_builder,
        }
        
        # 4. Call the underlying BAML function with all arguments
        return self.baml_fn(*args, **kwargs, baml_options=baml_options)

    def __repr__(self) -> str:
        return f"<magma.Prompt name='{self.name}' baml_fn='{self.baml_fn.__name__}'>"