# import pytest
# from unittest.mock import MagicMock, patch, ANY

# mock_registry = MagicMock()
# mock_registry.add_prompt = MagicMock()

# with patch.dict('sys.modules', {'magma.registry': mock_registry}):
#     from magma.prompts import Prompt
#     from magma.models import Model
#     from magma.tools import Tool

# # Mock the BAML client and its components
# mock_baml_fn = MagicMock(return_value="BAML response")
# mock_baml_client_registry = MagicMock()
# mock_baml_type_builder = MagicMock()
# mock_baml_type_builder.add_baml = MagicMock()

# @pytest.fixture
# def clean_mocks():
#     """Reset mocks before each test."""
#     mock_registry.reset_mock()
#     mock_registry.add_prompt.reset_mock()
#     mock_baml_fn.reset_mock()
#     mock_baml_type_builder.add_baml.reset_mock()

# def test_prompt_initialization_and_registration(clean_mocks):
#     """Tests that a Prompt registers itself upon creation."""
#     prompt = Prompt(baml_fn=mock_baml_fn, name="my_prompt")
#     assert prompt.baml_fn is mock_baml_fn
#     assert prompt.name == "my_prompt"
#     mock_registry.add_prompt.assert_called_once_with("my_prompt", prompt)

# @patch('baml_py.ClientRegistry', return_value=mock_baml_client_registry)
# @patch('baml_client.TypeBuilder', return_value=mock_baml_type_builder)
# def test_prompt_execution_with_context(mock_tb_class, mock_cr_class, clean_mocks):
#     """
#     Tests the core logic of executing a prompt with dynamic context
#     (models and tools) provided by the agent orchestrator.
#     """
#     # 1. Setup mock components
#     mock_model = MagicMock(spec=Model)
#     # The to_baml_client method is crucial for the integration
#     mock_model.to_baml_client.return_value = mock_baml_client_registry

#     mock_tool = MagicMock(spec=Tool)
#     # The tool needs a method to provide its BAML schema
#     mock_tool.to_baml_schema.return_value = "class MyMockTool { arg: string }"

#     # 2. Create the Prompt instance
#     prompt = Prompt(baml_fn=mock_baml_fn, name="test_prompt")

#     # 3. Simulate the agent calling the prompt's internal execute method
#     query_kwargs = {"query": "What is the weather?"}
#     prompt._execute_with_context(
#         model=mock_model,
#         tools=[mock_tool],
#         **query_kwargs
#     )

#     # 4. Assert the BAML function was called correctly
#     # It should receive the original query kwargs AND the baml_options
#     mock_model.to_baml_client.assert_called_once()
#     mock_baml_type_builder.add_baml.assert_called_once_with("class MyMockTool { arg: string }")

#     expected_baml_options = {
#         "client_registry": mock_baml_client_registry,
#         "tb": mock_baml_type_builder,
#     }
    
#     mock_baml_fn.assert_called_once_with(
#         query="What is the weather?",
#         baml_options=expected_baml_options
#     )

# def test_prompt_direct_call_fails_gracefully(clean_mocks):
#     """
#     Tests that calling a prompt directly without the agent context
#     raises a clear error.
#     """
#     prompt = Prompt(baml_fn=mock_baml_fn, name="direct_call_prompt")
#     with pytest.raises(RuntimeError, match="A magma.Prompt must be called from within an active magma.Agent execution"):
#         prompt(query="This should fail")


import pytest
from unittest.mock import MagicMock, patch

# Mock the registry that prompts.py will import
mock_registry = MagicMock()
mock_registry.add_prompt = MagicMock()

# Mock the BAML modules that prompts.py will import.
# The paths must match where they are imported *in the file under test*.
@patch.dict('sys.modules', {
    'magma.registry': mock_registry,
    'baml_py': MagicMock(),
    'baml_client.type_builder': MagicMock(),
})
def test_prompt_initialization_and_registration():
    """
    Tests that a Prompt initializes correctly and registers itself if a name is given.
    """
    # We must import inside the patched context
    from magma.prompts import Prompt

    mock_registry.add_prompt.reset_mock()
    mock_baml_fn = MagicMock()

    # Test case 1: Initialization with a name
    prompt = Prompt(baml_fn=mock_baml_fn, name="my_prompt")
    assert prompt.baml_fn is mock_baml_fn
    assert prompt.name == "my_prompt"
    mock_registry.add_prompt.assert_called_once_with("my_prompt", prompt)

    # Test case 2: Initialization without a name (no registration)
    mock_registry.add_prompt.reset_mock()
    prompt_no_name = Prompt(baml_fn=mock_baml_fn)
    assert prompt_no_name.name is None
    mock_registry.add_prompt.assert_not_called()


@patch('magma.prompts.TypeBuilder')
@patch('magma.prompts.ClientRegistry')
def test_prompt_execution_with_context(MockClientRegistry, MockTypeBuilder):
    """
    Tests the internal execution logic with dynamic context (models and tools).
    """
    from magma.prompts import Prompt, Model, Tool

    # Arrange: Setup mock BAML components and Magma objects
    mock_baml_fn = MagicMock(return_value="BAML response")
    mock_cr_instance = MockClientRegistry.return_value
    mock_tb_instance = MockTypeBuilder.return_value
    mock_tb_instance.add_baml = MagicMock()

    mock_model = MagicMock(spec=Model)
    mock_model.to_baml_client.return_value = mock_cr_instance

    mock_tool = MagicMock(spec=Tool)
    mock_tool.to_baml_schema.return_value = "class MyMockTool { arg: string }"
    
    prompt = Prompt(baml_fn=mock_baml_fn, name="test_prompt")
    query_kwargs = {"query": "What is the weather?"}

    # Act: Call the internal method, simulating the agent orchestrator
    result = prompt._execute_with_context(
        model=mock_model,
        tools=[mock_tool],
        **query_kwargs
    )

    # Assert
    assert result == "BAML response"
    mock_model.to_baml_client.assert_called_once()
    MockClientRegistry.assert_called_once()
    MockTypeBuilder.assert_called_once()
    mock_tb_instance.add_baml.assert_called_once_with("class MyMockTool { arg: string }")

    expected_baml_options = {
        "client_registry": mock_cr_instance,
        "tb": mock_tb_instance,
    }
    mock_baml_fn.assert_called_once_with(
        query="What is the weather?",
        baml_options=expected_baml_options
    )


@patch('magma.prompts.TypeBuilder')
@patch('magma.prompts.ClientRegistry')
def test_prompt_execution_without_tools(MockClientRegistry, MockTypeBuilder):
    """Tests execution works correctly when no tools are provided."""
    from magma.prompts import Prompt, Model
    
    # Arrange
    mock_baml_fn = MagicMock()
    mock_cr_instance = MockClientRegistry.return_value
    mock_tb_instance = MockTypeBuilder.return_value
    mock_tb_instance.add_baml = MagicMock()

    mock_model = MagicMock(spec=Model)
    mock_model.to_baml_client.return_value = mock_cr_instance

    prompt = Prompt(baml_fn=mock_baml_fn)

    # Act
    prompt._execute_with_context(model=mock_model, tools=[], query="test")

    # Assert
    mock_model.to_baml_client.assert_called_once()
    mock_tb_instance.add_baml.assert_not_called()
    mock_baml_fn.assert_called_once_with(
        query="test",
        baml_options={"client_registry": mock_cr_instance, "tb": mock_tb_instance}
    )


def test_prompt_direct_call_fails_gracefully():
    """
    Tests that calling a prompt directly without the agent context raises a clear error.
    """
    from magma.prompts import Prompt
    
    prompt = Prompt(baml_fn=MagicMock(), name="direct_call_prompt")
    
    with pytest.raises(RuntimeError, match="A magma.Prompt cannot be called directly"):
        prompt(query="This should fail")