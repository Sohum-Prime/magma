import pytest
import inspect
from unittest.mock import MagicMock, patch

# Mock the registry before importing the module to be tested
mock_registry = MagicMock()
mock_registry.add_tool = MagicMock()

with patch.dict('sys.modules', {'magma.registry': mock_registry}):
    from magma.tools import tool, Tool

@pytest.fixture(autouse=True)
def clean_registry():
    """Reset the registry mock before each test."""
    mock_registry.reset_mock()
    mock_registry.add_tool.reset_mock()

# --- Tests for the @tool decorator ---

@tool
def sample_tool_func(arg1: str, arg2: int = 10) -> str:
    """
    This is a sample tool.
    
    Args:
        arg1 (str): The first argument.
        arg2 (int): The second argument.
    """
    return f"{arg1}-{arg2}"

def test_tool_decorator_creates_tool_instance():
    """Tests that the decorator wraps the function in a Tool instance."""
    assert isinstance(sample_tool_func, Tool)
    assert sample_tool_func.name == "sample_tool_func"

def test_tool_decorator_registers_tool():
    """Tests that the decorator registers the tool with the global registry."""
    # The tool is registered at import time when the decorator is applied
    mock_registry.add_tool.assert_called_with("sample_tool_func", sample_tool_func)

def test_tool_invoke_calls_original_function():
    """Tests that invoking the decorated tool calls the original function."""
    result = sample_tool_func.invoke(arg1="test")
    assert result == "test-10"
    
    result_with_kwarg = sample_tool_func.invoke(arg1="hello", arg2=5)
    assert result_with_kwarg == "hello-5"

def test_tool_generates_correct_baml_schema():
    """Tests the automatic generation of the BAML schema string."""
    schema = sample_tool_func.to_baml_schema()
    
    # Normalize whitespace for consistent comparison
    expected_schema = """
    class sample_tool_func @description("This is a sample tool.") {
      arg1 string @description("The first argument.")
      arg2 int @description("The second argument.")
    }
    """
    assert inspect.cleandoc(schema) == inspect.cleandoc(expected_schema)

def test_tool_docstring_parsing_failure():
    """Tests that a tool with a malformed docstring raises an error."""
    with pytest.raises(ValueError, match="Docstring for tool 'bad_tool' is missing 'Args:' section"):
        @tool
        def bad_tool(arg1: str):
            """This docstring is bad."""
            pass

# --- Tests for from_langchain wrapper ---

def test_from_langchain_wrapper():
    """Tests creating a magma.Tool from a mock LangChain tool."""
    # Create a mock LangChain tool with the expected attributes
    mock_lc_tool = MagicMock()
    mock_lc_tool.name = "langchain_search"
    mock_lc_tool.description = "A search tool from LangChain."
    
    # Mock the Pydantic model for args_schema
    class MockArgsSchema(MagicMock):
        # Pydantic models have a `model_fields` attribute
        model_fields = {
            "query": MagicMock(description="The search query", annotation=str),
        }
    mock_lc_tool.args_schema = MockArgsSchema
    
    # Create the magma.Tool using the class method
    magma_search_tool = Tool.from_langchain(mock_lc_tool)
    
    # Assertions
    assert isinstance(magma_search_tool, Tool)
    assert magma_search_tool.name == "langchain_search"
    assert "A search tool from LangChain" in magma_search_tool.description
    
    # Check the generated BAML schema
    schema = magma_search_tool.to_baml_schema()
    expected_schema = """
    class langchain_search @description("A search tool from LangChain.") {
      query string @description("The search query")
    }
    """
    assert inspect.cleandoc(schema) == inspect.cleandoc(expected_schema)