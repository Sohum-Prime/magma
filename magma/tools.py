import inspect
import types
from typing import Callable, Any, Dict, List
from functools import wraps

try:
    from magma import registry
except ImportError:
    # Provide a dummy for environments where the full package isn't installed.
    class DummyRegistry:
        def add_tool(self, name: str, tool: Any): pass
    registry = DummyRegistry()

try:                            
    from huggingface_hub import hf_hub_download, get_collection
except ImportError:             
    hf_hub_download = None
    get_collection = None

try:                            
    from gradio_client import Client
except ImportError:
    Client = None

# A mapping from Python types to BAML types for schema generation
_TYPE_MAP = {
    str: "string",
    int: "int",
    float: "float",
    bool: "bool",
    list: "string[]",
    dict: "map<string, string>",
}

class Tool:
    """Base class for a capability that can be executed by an agent."""
    def __init__(self, name: str, func: Callable, description: str, params: Dict):
        self.name = name
        self.func = func
        self.description = description
        self.params = params
        registry.add_tool(self.name, self)

    def invoke(self, *args, **kwargs) -> Any:
        """Executes the tool's underlying function."""
        # Handle case where args are passed as a single dictionary (e.g., from LangGraph)
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            return self.func(**args[0])
        return self.func(*args, **kwargs)

    def to_baml_schema(self) -> str:
        """Generates a BAML class definition string for this tool."""
        main_desc = self.description.split('\n')[0].strip().replace('"', '\\"')
        schema = f'class {self.name} @description("{main_desc}") {{\n'
        for name, details in self.params.items():
            baml_type = _TYPE_MAP.get(details.get("type"), "string")
            param_desc = details.get("description", "").replace('"', '\\"')
            schema += f'  {name} {baml_type} @description("{param_desc}")\n'
        schema += '}'
        return schema

    @classmethod
    def from_langchain(cls, lc_tool: Any) -> "Tool":
        """Creates a magma.Tool from a LangChain tool instance."""
        params = {}
        if hasattr(lc_tool, 'args_schema') and hasattr(lc_tool.args_schema, 'model_fields'):
            for name, field in lc_tool.args_schema.model_fields.items():
                params[name] = {"type": field.annotation, "description": field.description or ""}
        
        func_to_wrap = getattr(lc_tool, '_run', lc_tool.run)
        return cls(name=lc_tool.name, func=func_to_wrap, description=lc_tool.description, params=params)

    @classmethod
    def from_code(cls, tool_code: str, **kwargs) -> "Tool":
        """Creates a magma.Tool instance from a string of Python code."""
        module = types.ModuleType("dynamic_tool")
        exec(tool_code, module.__dict__)
        # Find the first class in the executed code that is a subclass of Tool
        tool_class = next((obj for _, obj in inspect.getmembers(module, inspect.isclass) if issubclass(obj, Tool) and obj is not Tool), None)
        if tool_class is None:
            raise ValueError("No Tool subclass found in the provided code.")
        return tool_class(**kwargs)

    @classmethod
    def from_hub(cls, repo_id: str, trust_remote_code: bool = False, **kwargs) -> "Tool":
        """Loads a magma.Tool from a Hugging Face Space repository."""
        if not trust_remote_code:
            raise ValueError("Loading a tool from the Hub requires `trust_remote_code=True`.")
        if hf_hub_download is None:
            raise ImportError("Please install `huggingface-hub` to use `from_hub`.")
        
        # Download the tool.py file from the root of the Space
        tool_file = hf_hub_download(repo_id, "tool.py", repo_type="space", **kwargs)
        with open(tool_file, 'r', encoding='utf-8') as f:
            code = f.read()
        return cls.from_code(code)

    @classmethod
    def from_space(cls, space_id: str, name: str, description: str, **kwargs) -> "Tool":
        """Creates a magma.Tool by wrapping a live Gradio Space API."""
        if Client is None:
            raise ImportError("Please install `gradio_client` to use `from_space`.")

        client = Client(space_id, **kwargs)
        api_info = client.view_api(print_info=False, return_format="dict")
        
        endpoint_info = next((e for e in api_info.get("named_endpoints", {}).values()), None)
        if not endpoint_info:
            raise ValueError(f"Could not find a valid API endpoint in Gradio Space '{space_id}'.")

        params = {p["parameter_name"]: {"type": str, "description": p.get("label", "")} for p in endpoint_info.get("parameters", []) if not p.get("parameter_has_default")}

        def invoke_wrapper(*args, **kwargs):
            # Gradio client predict can take positional or keyword args
            if args:
                 return client.predict(api_name=endpoint_info["name"], *args)
            return client.predict(api_name=endpoint_info["name"], **kwargs)

        return cls(name=name, func=invoke_wrapper, description=description, params=params)

    def __repr__(self):
        return f"<magma.Tool name='{self.name}'>"

def tool(func: Callable) -> Tool:
    """Decorator to transform a Python function into a magma.Tool."""
    docstring = inspect.getdoc(func)
    if not docstring or "Args:" not in docstring:
        raise ValueError(f"Docstring for tool '{func.__name__}' is missing 'Args:' section.")

    description, args_part = docstring.split("Args:", 1)
    description = description.strip()
    sig = inspect.signature(func)
    params, arg_docs = {}, {}

    for line in args_part.strip().split('\n'):
        line = line.strip()
        if '(' in line and ')' in line:
            arg_name = line.split('(')[0].strip()
            arg_desc = line.split(':', 1)[1].strip() if ':' in line else ""
            arg_docs[arg_name] = arg_desc

    for name, param in sig.parameters.items():
        if param.annotation is inspect.Parameter.empty:
            raise TypeError(f"Tool '{func.__name__}' missing type hint for parameter '{name}'.")
        params[name] = {"type": param.annotation, "description": arg_docs.get(name, "")}

    # The decorator returns an instance of the Tool class, which registers itself.
    return Tool(name=func.__name__, func=func, description=description, params=params)

class ToolCollection:
    """A class for managing a list of tools, especially when loaded from the Hub."""
    def __init__(self, tools: List[Tool]):
        self.tools = tools

    @classmethod
    def from_hub(cls, collection_slug: str, trust_remote_code: bool = False, **kwargs) -> "ToolCollection":
        """Loads a collection of tools from a Hugging Face collection."""
        if not trust_remote_code:
            raise ValueError("Loading a collection from the Hub requires `trust_remote_code=True`.")
        if get_collection is None:
            raise ImportError("Please install `huggingface-hub` to use `ToolCollection.from_hub`.")

        collection = get_collection(collection_slug, **kwargs)
        tool_repos = [item.item_id for item in collection.items if item.item_type == "space"]
        
        # For each repo in the collection, load the tool from the hub
        tools = [Tool.from_hub(repo_id, trust_remote_code=True) for repo_id in tool_repos]
        return cls(tools)