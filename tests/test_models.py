# import pytest
# from unittest.mock import patch, MagicMock

# # Mock the registry before importing the module to be tested
# # This ensures our tests don't have side effects on a real registry
# mock_registry = MagicMock()
# mock_registry.add_model = MagicMock()

# # We need the real BAML ClientRegistry for testing the conversion
# from baml_py import ClientRegistry

# # Since we are testing 'models.py', we patch the global registry it will try to import and use.
# with patch.dict('sys.modules', {'magma.registry': mock_registry}):
#     from magma.models import Model

# @pytest.fixture(autouse=True)
# def reset_mocks():
#     """Reset mocks before each test to ensure isolation."""
#     mock_registry.reset_mock()
#     mock_registry.add_model.reset_mock()

# def test_model_basic_initialization():
#     """Tests that a model can be created with only an ID."""
#     model = Model(id="openai/gpt-4o")
#     assert model.id == "openai/gpt-4o"
#     assert model.params == {}
#     mock_registry.add_model.assert_called_once_with(model)

# def test_model_initialization_with_params():
#     """Tests that a model correctly stores additional kwargs."""
#     model = Model(
#         id="anthropic/claude-3-haiku-20240307",
#         temperature=0.7,
#         max_tokens=1024
#     )
#     assert model.id == "anthropic/claude-3-haiku-20240307"
#     assert model.params == {"temperature": 0.7, "max_tokens": 1024}
#     mock_registry.add_model.assert_called_once_with(model)

# def test_to_baml_client_openai():
#     """Tests conversion to a BAML ClientRegistry for an OpenAI model."""
#     model = Model(id="openai/gpt-4o", api_key="sk-test", temperature=0.0)
    
#     baml_cr = model.to_baml_client()
    
#     assert isinstance(baml_cr, ClientRegistry)
    
#     # Check that the primary client is set correctly
#     client = baml_cr.add_llm_client("magma-client")
#     assert client is not None
#     assert baml_cr.primary == "magma-client"
    
#     # Check the client's configuration
#     assert client.provider == "openai"
#     expected_options = {
#         "model": "gpt-4o",
#         "api_key": "sk-test",
#         "temperature": 0.0,
#     }
#     assert client.options == expected_options

# def test_to_baml_client_ollama():
#     """Tests conversion for a local model like Ollama."""
#     model = Model(id="ollama/llama3", api_base="http://localhost:11434")
    
#     baml_cr = model.to_baml_client()
#     client = baml_cr.add_llm_client("magma-client")
    
#     assert client is not None
#     # BAML uses 'openai-generic' for OpenAI-compatible APIs like Ollama's
#     assert client.provider == "openai-generic"
#     expected_options = {
#         "model": "llama3",
#         "api_base": "http://localhost:11434",
#     }
#     assert client.options == expected_options

# def test_to_baml_client_azure():
#     """Tests conversion for a more complex provider like Azure OpenAI."""
#     model = Model(
#         id="azure/my-deployment",
#         api_base="https://my-endpoint.openai.azure.com/",
#         api_version="2024-02-01",
#         api_key="azure-key"
#     )
    
#     baml_cr = model.to_baml_client()
#     client = baml_cr.add_llm_client("magma-client")
    
#     assert client is not None
#     assert client.provider == "azure-openai"
#     expected_options = {
#         # Note: for Azure, the full ID is used as the model name by LiteLLM, 
#         # but BAML's azure-openai provider expects the deployment name.
#         # Our implementation should correctly pass the deployment name.
#         "model": "my-deployment",
#         "api_base": "https://my-endpoint.openai.azure.com/",
#         "api_version": "2024-02-01",
#         "api_key": "azure-key",
#     }
#     assert client.options == expected_options

import pytest
from unittest.mock import patch, MagicMock

# We need the real BAML ClientRegistry for type checking and for the mock's spec
try:
    from baml_py import ClientRegistry
except ImportError:
    # If baml_py is not installed, create a dummy class for type hinting
    class ClientRegistry:
        pass

# We use patch on 'magma.models.registry' to ensure we replace the correct object.
# A fixture could also be used to apply this patch to all tests automatically.
@patch('magma.models.registry', new_callable=MagicMock)
def test_model_basic_initialization(mock_registry):
    """Tests that a model can be created with only an ID."""
    from magma.models import Model
    model = Model(id="openai/gpt-4o")
    assert model.id == "openai/gpt-4o"
    assert model.params == {}
    # Assert that add_model was called with the ID and the model instance
    mock_registry.add_model.assert_called_once_with("openai/gpt-4o", model)

@patch('magma.models.registry', new_callable=MagicMock)
def test_model_initialization_with_params(mock_registry):
    """Tests that a model correctly stores additional kwargs."""
    from magma.models import Model
    model = Model(
        id="anthropic/claude-3-haiku-20240307",
        temperature=0.7,
        max_tokens=1024
    )
    assert model.id == "anthropic/claude-3-haiku-20240307"
    assert model.params == {"temperature": 0.7, "max_tokens": 1024}
    # Assert that add_model was called with the ID and the model instance
    mock_registry.add_model.assert_called_once_with("anthropic/claude-3-haiku-20240307", model)

# We patch ClientRegistry within the models module to intercept its instantiation
@patch('magma.models.ClientRegistry', new_callable=MagicMock)
def test_to_baml_client_openai(MockClientRegistry):
    """Tests conversion to a BAML ClientRegistry for an OpenAI model."""
    from magma.models import Model
    
    # Arrange
    mock_cr_instance = MockClientRegistry.return_value
    model = Model(id="openai/gpt-4o", api_key="sk-test", temperature=0.0)
    
    # Act
    baml_cr = model.to_baml_client()
    
    # Assert
    assert baml_cr is mock_cr_instance
    MockClientRegistry.assert_called_once()
    
    mock_cr_instance.add_llm_client.assert_called_once_with(
        name="magma-client",
        provider="openai",
        options={
            "model": "gpt-4o",
            "api_key": "sk-test",
            "temperature": 0.0,
        }
    )
    mock_cr_instance.set_primary.assert_called_once_with("magma-client")

@patch('magma.models.ClientRegistry', new_callable=MagicMock)
def test_to_baml_client_ollama(MockClientRegistry):
    """Tests conversion for a local model like Ollama."""
    from magma.models import Model

    # Arrange
    mock_cr_instance = MockClientRegistry.return_value
    model = Model(id="ollama/llama3", api_base="http://localhost:11434")
    
    # Act
    baml_cr = model.to_baml_client()

    # Assert
    assert baml_cr is mock_cr_instance
    MockClientRegistry.assert_called_once()

    mock_cr_instance.add_llm_client.assert_called_once_with(
        name="magma-client",
        provider="openai-generic",
        options={
            "model": "llama3",
            "api_base": "http://localhost:11434",
        }
    )
    mock_cr_instance.set_primary.assert_called_once_with("magma-client")

@patch('magma.models.ClientRegistry', new_callable=MagicMock)
def test_to_baml_client_azure(MockClientRegistry):
    """Tests conversion for a more complex provider like Azure OpenAI."""
    from magma.models import Model

    # Arrange
    mock_cr_instance = MockClientRegistry.return_value
    model = Model(
        id="azure/my-deployment",
        api_base="https://my-endpoint.openai.azure.com/",
        api_version="2024-02-01",
        api_key="azure-key"
    )
    
    # Act
    baml_cr = model.to_baml_client()
    
    # Assert
    assert baml_cr is mock_cr_instance
    MockClientRegistry.assert_called_once()

    mock_cr_instance.add_llm_client.assert_called_once_with(
        name="magma-client",
        provider="azure-openai",
        options={
            "model": "my-deployment",
            "api_base": "https://my-endpoint.openai.azure.com/",
            "api_version": "2024-02-01",
            "api_key": "azure-key",
        }
    )
    mock_cr_instance.set_primary.assert_called_once_with("magma-client")