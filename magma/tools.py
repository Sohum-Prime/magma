import inspect
from typing import Callable, Any, Dict, Type
from functools import wraps

try:
    from magma.registry import registry
except ImportError:
    class DummyRegistry:
        def add_tool(self, name, tool): pass
    registry = DummyRegistry()

# A mapping from Python types to BAML types for schema generation
_TYPE_MAP = {
    str: "string",
    int: "int",
    float: "float",
    bool: "bool",
    list: "string[]", # Default list to string array, can be enhanced
    dict: "map<string, string>", # Default map, can be enhanced
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
        return self.func(*args, **kwargs)

    def to_baml_schema(self) -> str:
        """Generates a BAML class definition string for this tool."""
        # Main description from the first line of the docstring
        main_desc = self.description.split('\n')[0].strip().replace('"', '\\"')
        
        schema = f'class {self.name} @description("{main_desc}") {{\n'
        for name, details in self.params.items():
            baml_type = _TYPE_MAP.get(details["type"], "string")
            param_desc = details.get("description", "").replace('"', '\\"')
            schema += f'  {name} {baml_type} @description("{param_desc}")\n'
        schema += '}'
        return schema

    @classmethod
    def from_langchain(cls, lc_tool: Any) -> "Tool":
        """Creates a magma.Tool from a LangChain tool instance."""
        name = lc_tool.name
        description = lc_tool.description
        
        params = {}
        if hasattr(lc_tool, 'args_schema') and hasattr(lc_tool.args_schema, 'model_fields'):
            for field_name, field_info in lc_tool.args_schema.model_fields.items():
                params[field_name] = {
                    "type": field_info.annotation,
                    "description": field_info.description or ""
                }

        # The wrapped function will be the LangChain tool's own `_run` or `run` method
        func_to_wrap = getattr(lc_tool, '_run', lc_tool.run)
        
        return cls(name=name, func=func_to_wrap, description=description, params=params)

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
    params = {}
    
    # Parse args from docstring
    arg_docs = {}
    for line in args_part.strip().split('\n'):
        line = line.strip()
        if '(' in line and ')' in line:
            arg_name = line.split('(')[0].strip()
            arg_desc = line.split(':', 1)[1].strip() if ':' in line else ""
            arg_docs[arg_name] = arg_desc

    for name, param in sig.parameters.items():
        if param.annotation is inspect.Parameter.empty:
            raise TypeError(f"Tool '{func.__name__}' missing type hint for parameter '{name}'.")
        
        params[name] = {
            "type": param.annotation,
            "description": arg_docs.get(name, "")
        }

    # The decorator returns an instance of the Tool class
    tool_instance = Tool(name=func.__name__, func=func, description=description, params=params)
    
    # To make it feel like a function, we can add a wrapper
    @wraps(func)
    def wrapper(*args, **kwargs):
        return tool_instance.invoke(*args, **kwargs)

    # Attach the Tool instance to the wrapper so it can be accessed
    wrapper.tool_instance = tool_instance
    
    # Return the tool instance itself, as per the tests
    return tool_instance