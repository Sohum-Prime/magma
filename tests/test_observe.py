import pytest
from unittest.mock import MagicMock, patch, ANY

# This is a complex test setup because we are mocking multiple
# global-state libraries (litellm, langfuse) that are configured
# by our code.

# Mock Langfuse and its components before any magma imports
mock_langfuse_instance = MagicMock()
mock_langfuse_instance.shutdown = MagicMock()
mock_langfuse_callback_handler = MagicMock()

# Mock the main Langfuse class and get_client function
mock_langfuse_class = MagicMock(return_value=mock_langfuse_instance)
mock_get_client = MagicMock(return_value=mock_langfuse_instance)

# Mock the Langfuse callback handler for LangGraph
mock_langfuse_callback_module = MagicMock()
mock_langfuse_callback_module.LangfuseCallbackHandler = MagicMock(return_value=mock_langfuse_callback_handler)

# Mock the @observe decorator
mock_observe_decorator = MagicMock(wraps=lambda f: f)

# Apply patches
@patch.dict('sys.modules', {
    'langfuse': MagicMock(Langfuse=mock_langfuse_class, get_client=mock_get_client, observe=mock_observe_decorator),
    'langfuse.langchain': mock_langfuse_callback_module,
    'litellm': MagicMock()
})
def test_agent_initialization_with_langfuse_env_vars():
    """
    Tests that the Agent class correctly initializes Langfuse and configures
    LiteLLM when environment variables are present.
    """
    import litellm
    from magma.agent import Agent # Import Agent after patching

    # Simulate environment variables being set
    with patch.dict('os.environ', {
        'LANGFUSE_PUBLIC_KEY': 'pk-test',
        'LANGFUSE_SECRET_KEY': 'sk-test'
    }):
        # Instantiate the agent
        agent = Agent(state=MagicMock())

        # Assert that Langfuse was initialized
        mock_langfuse_class.assert_called_once()

        # Assert that LiteLLM callbacks were set correctly
        assert litellm.success_callback == ["langfuse"]
        assert litellm.failure_callback == ["langfuse"]

@patch.dict('sys.modules', {
    'langfuse': MagicMock(Langfuse=mock_langfuse_class, get_client=mock_get_client, observe=mock_observe_decorator),
    'langfuse.langchain': mock_langfuse_callback_module,
})
def test_agent_compile_configures_langgraph_callback():
    """
    Tests that agent.compile() injects the LangfuseCallbackHandler.
    """
    from magma.agent import Agent

    # Mock the underlying StateGraph and its compile method
    mock_graph = MagicMock()
    mock_app = MagicMock()
    mock_graph.compile.return_value = mock_app

    with patch('langgraph.graph.StateGraph', return_value=mock_graph):
        with patch.dict('os.environ', {
            'LANGFUSE_PUBLIC_KEY': 'pk-test',
            'LANGFUSE_SECRET_KEY': 'sk-test'
        }):
            agent = Agent(state=MagicMock())
            compiled_app = agent.compile()

            # Check that compile was called with the handler in its config
            mock_graph.compile.assert_called_once_with(
                checkpointer=None,
                interrupt_before=None,
                interrupt_after=None,
                callbacks=[mock_langfuse_callback_handler]
            )
            assert compiled_app is mock_app

def test_trace_decorator_is_alias_for_langfuse_observe():
    """
    Tests that @magma.trace is a direct reference to langfuse.observe.
    """
    from magma.observe import trace
    from langfuse import observe

    assert trace is observe

@patch.dict('sys.modules', {
    'langfuse': MagicMock(observe=mock_observe_decorator),
})
def test_trace_decorator_usage():
    """
    Tests that using the @magma.trace decorator calls the underlying
    langfuse.observe decorator.
    """
    from magma.observe import trace
    
    @trace
    def my_traced_function():
        return "hello"

    # The decorator is applied at function definition time.
    # We check that our mock was used to wrap the function.
    mock_observe_decorator.assert_called_with(my_traced_function)