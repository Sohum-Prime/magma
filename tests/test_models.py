import pytest
from unittest.mock import patch, MagicMock

# Mock the registry before importing the module to be tested
# This ensures our tests don't have side effects on a real registry
mock_registry = MagicMock()
mock_registry.add_model = MagicMock()

# Since we are testing 'models.py', we patch the global registry it will try to import and use.
# We assume the registry will live in 'magma.registry'.
with patch.dict('sys.modules', {'magma.registry': mock_registry}):
    from magma.models import Model

# We need the real BAML ClientRegistry for testing the conversion
from baml_py import ClientRegistry

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test to ensure isolation."""
    mock_registry.reset_mock()
    mock_registry.add_model.reset_mock()

def test_model_basic_initialization():
    """Tests that a model can be created with only an ID."""
    model = Model(id="openai/gpt-4o")
    assert model.id == "openai/gpt-4o"
    assert model.params == {}
    mock_registry.add_model.assert_called_once_with(model)

def test_model_initialization_with_params():
    """Tests that a model correctly stores additional kwargs."""
    model = Model(
        id="anthropic/claude-3-haiku-20240307",
        temperature=0.7,
        max_tokens=1024
    )
    assert model.id == "anthropic/claude-3-haiku-20240307"
    assert model.params == {"temperature": 0.7, "max_tokens": 1024}
    mock_registry.add_model.assert_called_once_with(model)

def test_to_baml_client_openai():
    """Tests conversion to a BAML ClientRegistry for an OpenAI model."""
    model = Model(id="openai/gpt-4o", api_key="sk-test", temperature=0.0)
    
    baml_cr = model.to_baml_client()
    
    assert isinstance(baml_cr, ClientRegistry)
    
    # Check that the primary client is set correctly
    client = baml_cr.get_llm_client("magma-client")
    assert client is not None
    assert baml_cr.primary == "magma-client"
    
    # Check the client's configuration
    assert client.provider == "openai"
    expected_options = {
        "model": "gpt-4o",
        "api_key": "sk-test",
        "temperature": 0.0,
    }
    assert client.options == expected_options

def test_to_baml_client_ollama():
    """Tests conversion for a local model like Ollama."""
    model = Model(id="ollama/llama3", api_base="http://localhost:11434")
    
    baml_cr = model.to_baml_client()
    client = baml_cr.get_llm_client("magma-client")
    
    assert client is not None
    # BAML uses 'openai-generic' for OpenAI-compatible APIs like Ollama's
    assert client.provider == "openai-generic"
    expected_options = {
        "model": "llama3",
        "api_base": "http://localhost:11434",
    }
    assert client.options == expected_options

def test_to_baml_client_azure():
    """Tests conversion for a more complex provider like Azure OpenAI."""
    model = Model(
        id="azure/my-deployment",
        api_base="https://my-endpoint.openai.azure.com/",
        api_version="2024-02-01",
        api_key="azure-key"
    )
    
    baml_cr = model.to_baml_client()
    client = baml_cr.get_llm_client("magma-client")
    
    assert client is not None
    assert client.provider == "azure-openai"
    expected_options = {
        # Note: for Azure, the full ID is used as the model name by LiteLLM, 
        # but BAML's azure-openai provider expects the deployment name.
        # Our implementation should correctly pass the deployment name.
        "model": "my-deployment",
        "api_base": "https://my-endpoint.openai.azure.com/",
        "api_version": "2024-02-01",
        "api_key": "azure-key",
    }
    assert client.options == expected_options