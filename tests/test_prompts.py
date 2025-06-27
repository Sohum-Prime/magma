import pytest
from unittest.mock import MagicMock, patch, ANY

# Mock the registry before other imports
mock_registry = MagicMock()
mock_registry.add_prompt = MagicMock()

with patch.dict('sys.modules', {'magma.registry': mock_registry}):
    from magma.prompts import Prompt
    from magma.models import Model
    # Assuming a Tool class exists in magma.tools
    from magma.tools import Tool

# Mock the BAML client and its components
mock_baml_fn = MagicMock(return_value="BAML response")
mock_baml_client_registry = MagicMock()
mock_baml_type_builder = MagicMock()
mock_baml_type_builder.add_baml = MagicMock()

@pytest.fixture
def clean_mocks():
    """Reset mocks before each test."""
    mock_registry.reset_mock()
    mock_registry.add_prompt.reset_mock()
    mock_baml_fn.reset_mock()
    mock_baml_type_builder.add_baml.reset_mock()

def test_prompt_initialization_and_registration(clean_mocks):
    """Tests that a Prompt registers itself upon creation."""
    prompt = Prompt(baml_fn=mock_baml_fn, name="my_prompt")
    assert prompt.baml_fn is mock_baml_fn
    assert prompt.name == "my_prompt"
    mock_registry.add_prompt.assert_called_once_with("my_prompt", prompt)

@patch('baml_py.ClientRegistry', return_value=mock_baml_client_registry)
@patch('baml_client.TypeBuilder', return_value=mock_baml_type_builder)
def test_prompt_execution_with_context(mock_tb_class, mock_cr_class, clean_mocks):
    """
    Tests the core logic of executing a prompt with dynamic context
    (models and tools) provided by the agent orchestrator.
    """
    # 1. Setup mock components
    mock_model = MagicMock(spec=Model)
    # The to_baml_client method is crucial for the integration
    mock_model.to_baml_client.return_value = mock_baml_client_registry

    mock_tool = MagicMock(spec=Tool)
    # The tool needs a method to provide its BAML schema
    mock_tool.to_baml_schema.return_value = "class MyMockTool { arg: string }"

    # 2. Create the Prompt instance
    prompt = Prompt(baml_fn=mock_baml_fn, name="test_prompt")

    # 3. Simulate the agent calling the prompt's internal execute method
    query_kwargs = {"query": "What is the weather?"}
    prompt._execute_with_context(
        model=mock_model,
        tools=[mock_tool],
        **query_kwargs
    )

    # 4. Assert the BAML function was called correctly
    # It should receive the original query kwargs AND the baml_options
    mock_model.to_baml_client.assert_called_once()
    mock_baml_type_builder.add_baml.assert_called_once_with("class MyMockTool { arg: string }")

    expected_baml_options = {
        "client_registry": mock_baml_client_registry,
        "tb": mock_baml_type_builder,
    }
    
    mock_baml_fn.assert_called_once_with(
        query="What is the weather?",
        baml_options=expected_baml_options
    )

def test_prompt_direct_call_fails_gracefully(clean_mocks):
    """
    Tests that calling a prompt directly without the agent context
    raises a clear error.
    """
    prompt = Prompt(baml_fn=mock_baml_fn, name="direct_call_prompt")
    with pytest.raises(RuntimeError, match="A magma.Prompt must be called from within an active magma.Agent execution"):
        prompt(query="This should fail")