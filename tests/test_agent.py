import pytest
from unittest.mock import MagicMock, patch, ANY
from typing import TypedDict

# Mock all external dependencies before importing the Agent class
mock_state_graph_instance = MagicMock()
mock_state_graph_class = MagicMock(return_value=mock_state_graph_instance)

mock_langfuse_callback_handler = MagicMock()
mock_langfuse_callback_module = MagicMock(CallbackHandler=MagicMock(return_value=mock_langfuse_callback_handler))

@patch.dict('sys.modules', {
    'langgraph.graph': MagicMock(StateGraph=mock_state_graph_class),
    'langfuse.langchain': mock_langfuse_callback_module,
    'litellm': MagicMock(),
    'magma.prompts': MagicMock(), # Mock prompts to break circular dependency
})
def test_agent_init_no_observability():
    """Tests agent initialization without LangFuse env vars."""
    import litellm
    from magma.agent import Agent
    
    Agent(state=MagicMock(), model=MagicMock())
    
    # Assert that callbacks were NOT set
    assert litellm.success_callback == []
    assert litellm.failure_callback == []

@patch.dict('sys.modules', {
    'langgraph.graph': MagicMock(StateGraph=mock_state_graph_class),
    'langfuse': MagicMock(),
    'langfuse.langchain': mock_langfuse_callback_module,
    'litellm': MagicMock(),
    'magma.prompts': MagicMock(),
})
def test_agent_init_with_observability():
    """Tests that agent init configures LangFuse and LiteLLM when env vars are set."""
    import litellm
    from magma.agent import Agent

    with patch.dict('os.environ', {'LANGFUSE_PUBLIC_KEY': 'pk-test', 'LANGFUSE_SECRET_KEY': 'sk-test'}):
        Agent(state=MagicMock(), model=MagicMock())
        assert litellm.success_callback == ["langfuse"]
        assert litellm.failure_callback == ["langfuse"]
    
    # Reset callbacks after test
    litellm.success_callback = []
    litellm.failure_callback = []

def test_add_node_wraps_function():
    """Tests that add_node calls the underlying graph's add_node with a wrapped function."""
    from magma.agent import Agent
    
    agent = Agent(state=MagicMock(), model=MagicMock())
    
    def original_node(state):
        return {}
        
    agent.add_node("test_node", original_node)
    
    # Assert that the internal graph's add_node was called, but with a new, wrapped callable
    mock_state_graph_instance.add_node.assert_called_once()
    args, _ = mock_state_graph_instance.add_node.call_args
    assert args[0] == "test_node"
    assert callable(args[1])
    assert args[1].__name__ == "context_wrapper" # Check that it's the wrapper

def test_compile_injects_callbacks():
    """Tests that compile adds the Langfuse callback handler if enabled."""
    from magma.agent import Agent
    
    with patch.dict('os.environ', {'LANGFUSE_PUBLIC_KEY': 'pk-test', 'LANGFUSE_SECRET_KEY': 'sk-test'}):
        agent = Agent(state=MagicMock(), model=MagicMock())
        agent.compile()
        
        # Check that the underlying graph's compile method was called with the handler
        mock_state_graph_instance.compile.assert_called_with(checkpointer=None, callbacks=[mock_langfuse_callback_handler])

def test_agent_context_is_set_during_node_execution():
    """Tests the core context management logic."""
    from magma.agent import Agent
    from magma.prompts import Prompt

    # Define a simple state
    class MyState(TypedDict):
        value: int

    # Mock model and tool
    mock_model = MagicMock()
    mock_tool = MagicMock()
    
    # This node will check the context
    def checking_node(state):
        # Assert that the context is set correctly inside the node
        assert Prompt._agent_context is not None
        assert Prompt._agent_context["model"] is mock_model
        assert Prompt._agent_context["tools"][0] is mock_tool
        return {}

    agent = Agent(state=MyState, model=mock_model, tools=[mock_tool])
    
    # Get the wrapped node function that the agent created
    agent.add_node("checking_node", checking_node)
    _, wrapped_node_func = mock_state_graph_instance.add_node.call_args[0]
    
    # Execute the wrapper directly to test its behavior
    assert Prompt._agent_context is None # Context should be None before the call
    wrapped_node_func({"value": 1})
    assert Prompt._agent_context is None # Context should be cleared after the call