import pytest
from unittest.mock import MagicMock

# Import the class and the singleton instance for testing
from magma.registry import Registry, registry as global_registry

@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure the global registry is clean before and after each test."""
    global_registry.clear()
    yield
    global_registry.clear()

def test_singleton_instance():
    """Tests that the global 'registry' is a single instance of the Registry class."""
    assert isinstance(global_registry, Registry)
    # Import it again to ensure it's the same object
    from magma.registry import registry as second_import
    assert global_registry is second_import

def test_add_and_get_model():
    """Tests adding and retrieving a model."""
    mock_model = MagicMock(name="gpt4o")
    global_registry.add_model("gpt4o", mock_model)
    assert len(global_registry.models) == 1
    assert global_registry.models["gpt4o"] is mock_model

def test_add_and_get_tool():
    """Tests adding and retrieving a tool."""
    mock_tool = MagicMock(name="get_weather")
    global_registry.add_tool("get_weather", mock_tool)
    assert len(global_registry.tools) == 1
    assert global_registry.tools["get_weather"] is mock_tool

def test_add_and_get_prompt():
    """Tests adding and retrieving a prompt."""
    mock_prompt = MagicMock(name="summarizer")
    global_registry.add_prompt("summarizer", mock_prompt)
    assert len(global_registry.prompts) == 1
    assert global_registry.prompts["summarizer"] is mock_prompt

def test_add_duplicate_model_raises_error():
    """Tests that adding a model with a duplicate name raises a ValueError."""
    mock_model_1 = MagicMock()
    global_registry.add_model("my_model", mock_model_1)
    
    with pytest.raises(ValueError, match="Model 'my_model' is already registered."):
        mock_model_2 = MagicMock()
        global_registry.add_model("my_model", mock_model_2)

def test_add_duplicate_tool_raises_error():
    """Tests that adding a tool with a duplicate name raises a ValueError."""
    mock_tool_1 = MagicMock()
    global_registry.add_tool("my_tool", mock_tool_1)
    
    with pytest.raises(ValueError, match="Tool 'my_tool' is already registered."):
        mock_tool_2 = MagicMock()
        global_registry.add_tool("my_tool", mock_tool_2)

def test_clear_method():
    """Tests that the clear() method removes all components."""
    global_registry.add_model("model1", MagicMock())
    global_registry.add_tool("tool1", MagicMock())
    global_registry.add_prompt("prompt1", MagicMock())

    assert len(global_registry.models) == 1
    assert len(global_registry.tools) == 1
    assert len(global_registry.prompts) == 1

    global_registry.clear()

    assert len(global_registry.models) == 0
    assert len(global_registry.tools) == 0
    assert len(global_registry.prompts) == 0

def test_properties_are_read_only_copies():
    """Tests that the component properties return copies, preventing direct modification."""
    models_dict = global_registry.models
    with pytest.raises(TypeError):
        # Dictionaries returned by properties should be immutable or copies
        # A simple way to test is to see if we can modify it.
        # A more robust implementation would use an immutable mapping.
        models_dict["new_model"] = MagicMock()
    
    # The original registry should be unchanged.
    assert "new_model" not in global_registry.models