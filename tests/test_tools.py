import pytest
import inspect
from unittest.mock import MagicMock, patch, mock_open

# Import the code to be tested
from magma.tools import tool, Tool, ToolCollection

# Common mock registry patcher to be used by tests
patch_registry = patch('magma.tools.registry', new_callable=MagicMock)

# --- Tests for the @tool decorator ---

@patch_registry
def test_tool_decorator_creates_tool_instance(mock_registry):
    """Tests that the decorator wraps the function in a Tool instance."""
    @tool
    def sample_tool_func(arg1: str, arg2: int = 10) -> str:
        """A sample tool.\nArgs:\n  arg1 (str): desc.\n  arg2 (int): desc."""
        return f"{arg1}-{arg2}"

    assert isinstance(sample_tool_func, Tool)
    assert sample_tool_func.name == "sample_tool_func"

@patch_registry
def test_tool_decorator_registers_tool(mock_registry):
    """Tests that the decorator registers the tool with the global registry."""
    @tool
    def sample_tool_func(arg1: str) -> str:
        """This is a sample tool.\nArgs:\n  arg1 (str): The first argument."""
        return arg1
    
    mock_registry.add_tool.assert_called_once_with("sample_tool_func", sample_tool_func)

@patch_registry
def test_tool_invoke_calls_original_function(mock_registry):
    """Tests that invoking the decorated tool calls the original function."""
    @tool
    def sample_tool_func(arg1: str, arg2: int = 10) -> str:
        """A sample tool.\nArgs:\n  arg1 (str): desc.\n  arg2 (int): desc."""
        return f"{arg1}-{arg2}"

    result = sample_tool_func.invoke(arg1="test")
    assert result == "test-10"
    
    result_with_kwarg = sample_tool_func.invoke(arg1="hello", arg2=5)
    assert result_with_kwarg == "hello-5"

@patch_registry
def test_tool_generates_correct_baml_schema(mock_registry):
    """Tests the automatic generation of the BAML schema string."""
    @tool
    def sample_tool_func(arg1: str, arg2: int = 10) -> str:
        """
        This is a sample tool.
        Args:
            arg1 (str): The first argument.
            arg2 (int): The second argument.
        """
        return f"{arg1}-{arg2}"

    schema = sample_tool_func.to_baml_schema()
    expected_schema = """
    class sample_tool_func @description("This is a sample tool.") {
      arg1 string @description("The first argument.")
      arg2 int @description("The second argument.")
    }
    """
    assert inspect.cleandoc(schema) == inspect.cleandoc(expected_schema)

@patch_registry
def test_tool_docstring_parsing_failure(mock_registry):
    """Tests that a tool with a malformed docstring raises an error."""
    with pytest.raises(ValueError, match="Docstring for tool 'bad_tool' is missing 'Args:' section"):
        @tool
        def bad_tool(arg1: str):
            """This docstring is bad."""
            pass

# --- Tests for Tool Classmethods ---

@patch_registry
def test_from_langchain_wrapper(mock_registry):
    """Tests creating a magma.Tool from a mock LangChain tool."""
    mock_lc_tool = MagicMock()
    mock_lc_tool.name = "langchain_search"
    mock_lc_tool.description = "A search tool from LangChain."
    
    # Mock the Pydantic-like args_schema
    mock_field = MagicMock(description="The search query", annotation=str)
    mock_lc_tool.args_schema.model_fields = {"query": mock_field}
    
    magma_search_tool = Tool.from_langchain(mock_lc_tool)
    
    assert isinstance(magma_search_tool, Tool)
    assert magma_search_tool.name == "langchain_search"
    mock_registry.add_tool.assert_called_once_with("langchain_search", magma_search_tool)
    
    schema = magma_search_tool.to_baml_schema()
    expected_schema = """
    class langchain_search @description("A search tool from LangChain.") {
      query string @description("The search query")
    }
    """
    assert inspect.cleandoc(schema) == inspect.cleandoc(expected_schema)

@patch_registry
def test_from_code(mock_registry):
    """Tests creating a tool from a code string."""
    tool_code = """
from magma.tools import Tool
class MyTestTool(Tool):
    def __init__(self):
        super().__init__(name="my_test_tool", func=self.run, description="A test tool.", params={"x": {"type": int}})
    def run(self, x: int):
        return x + 1
"""
    instance = Tool.from_code(tool_code)
    assert isinstance(instance, Tool)
    assert instance.name == "my_test_tool"
    mock_registry.add_tool.assert_called_once()
    assert instance.invoke(x=5) == 6

@patch('magma.tools.hf_hub_download')
@patch('builtins.open', new_callable=mock_open, read_data="""
from magma.tools import Tool
class MyHubTool(Tool):
    def __init__(self):
        super().__init__("hub_tool", lambda: "hub", "A tool from the hub", {})
""")
@patch_registry
def test_from_hub(mock_registry, mock_file_open, mock_hf_download):
    mock_hf_download.return_value = "path/to/downloaded/tool.py"
    with pytest.raises(ValueError, match="trust_remote_code=True"):
        Tool.from_hub("user/repo")
    instance = Tool.from_hub("user/repo", trust_remote_code=True)
    mock_hf_download.assert_called_once_with("user/repo", "tool.py", repo_type="space")
    assert instance.name == "hub_tool"
    assert instance.invoke() == "hub"
    
@patch('magma.tools.Client')
@patch_registry
def test_from_space(mock_registry, MockGradioClient):
    mock_client_instance = MockGradioClient.return_value
    mock_client_instance.view_api.return_value = {"named_endpoints": {"/predict": {"name": "/predict", "parameters": [{"parameter_name": "prompt", "label": "Your Prompt", "parameter_has_default": False}]}}}
    mock_client_instance.predict.return_value = "Generated Image"
    space_tool = Tool.from_space("user/space", "image_gen", "Generates images.")
    MockGradioClient.assert_called_once_with("user/space")
    assert space_tool.name == "image_gen"
    assert "prompt" in space_tool.params
    result = space_tool.invoke(prompt="A cat")
    mock_client_instance.predict.assert_called_once_with(api_name="/predict", prompt="A cat")
    assert result == "Generated Image"

# --- Tests for ToolCollection ---

@patch('magma.tools.get_collection')
@patch('magma.tools.Tool.from_hub')
def test_tool_collection_from_hub(MockToolFromHub, mock_get_collection):
    mock_collection = MagicMock()
    mock_item1 = MagicMock(item_id="user/tool1", item_type="space")
    mock_item2 = MagicMock(item_id="user/tool2", item_type="space")
    mock_collection.items = [mock_item1, mock_item2]
    mock_get_collection.return_value = mock_collection

    # Configure mocks to have a .name attribute that returns a string
    tool1_mock = MagicMock()
    tool1_mock.name = "tool1"
    tool2_mock = MagicMock()
    tool2_mock.name = "tool2"
    MockToolFromHub.side_effect = [tool1_mock, tool2_mock]

    with pytest.raises(ValueError, match="trust_remote_code=True"):
        ToolCollection.from_hub("user/my-collection")
    collection = ToolCollection.from_hub("user/my-collection", trust_remote_code=True)
    mock_get_collection.assert_called_once_with("user/my-collection")
    assert MockToolFromHub.call_count == 2
    assert len(collection.tools) == 2
    assert collection.tools[0].name == "tool1"