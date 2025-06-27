from typing import Dict, TYPE_CHECKING
from types import MappingProxyType
from collections.abc import Mapping

# Use TYPE_CHECKING to avoid circular imports at runtime,
# as Model, Tool, etc., will eventually import the registry.
if TYPE_CHECKING:
    from .models import Model
    from .tools import Tool
    from .prompts import Prompt

class Registry:
    """
    A central, singleton-like registry for discovering and storing all
    Magma components defined within an application's scope.
    """

    def __init__(self):
        self._models: Dict[str, "Model"] = {}
        self._tools: Dict[str, "Tool"] = {}
        self._prompts: Dict[str, "Prompt"] = {}

    @property
    def models(self) -> Mapping[str, "Model"]:
        """Provides a read-only view of the registered models."""
        return MappingProxyType(self._models)

    @property
    def tools(self) -> Mapping[str, "Tool"]:
        """Provides a read-only view of the registered tools."""
        return MappingProxyType(self._tools)

    @property
    def prompts(self) -> Mapping[str, "Prompt"]:
        """Provides a read-only view of the registered prompts."""
        return MappingProxyType(self._prompts)

    def add_model(self, name: str, model: "Model") -> None:
        """
        Registers a magma.Model instance.

        Raises:
            ValueError: If a model with the same name is already registered.
        """
        if name in self._models:
            raise ValueError(f"Model '{name}' is already registered.")
        self._models[name] = model

    def add_tool(self, name: str, tool: "Tool") -> None:
        """
        Registers a magma.Tool instance.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = tool

    def add_prompt(self, name: str, prompt: "Prompt") -> None:
        """
        Registers a magma.Prompt instance.

        Raises:
            ValueError: If a prompt with the same name is already registered.
        """
        if name in self._prompts:
            raise ValueError(f"Prompt '{name}' is already registered.")
        self._prompts[name] = prompt

    def clear(self) -> None:
        """
        Clears all registered components. Primarily for testing.
        """
        self._models.clear()
        self._tools.clear()
        self._prompts.clear()
        
    def __repr__(self) -> str:
        return (
            f"<MagmaRegistry: "
            f"{len(self._models)} models, "
            f"{len(self._tools)} tools, "
            f"{len(self._prompts)} prompts>"
        )

# Create the singleton instance that will be imported across the library.
registry = Registry()