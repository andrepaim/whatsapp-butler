import pytest
import asyncio
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
from agent.agent import load_agent_prompt, initialize_agent_and_runner, call_agent_async, APP_NAME
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from google.adk.events import Event, EventActions
from google.genai import types as genai_types # Alias to avoid conflict

# Define a constant for a valid webhook URL for testing
VALID_MCP_URL = "http://whatsapp-mcp-test:3001/mcp"

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("WHATSAPP_MCP_URL", VALID_MCP_URL)
    monkeypatch.setenv("AGENT_MODEL", "gemini-test-model")
    # Ensure QUERY_PREFIX has a default for tests if not set elsewhere
    monkeypatch.setenv("QUERY_PREFIX", "/query ")


def test_load_agent_prompt_success():
    prompt_content = "This is the test prompt."
    # Mock os.path.join to control the path being opened
    with patch('os.path.join', return_value='dummy/path/to/prompt.md') as mock_join:
        # Mock open to simulate reading from the prompt file
        with patch('builtins.open', mock_open(read_data=prompt_content)) as mock_file:
            prompt = load_agent_prompt()
            assert prompt == prompt_content
            mock_file.assert_called_once_with('dummy/path/to/prompt.md', 'r')
            # Check that os.path.join was called correctly (optional, but good for robustness)
            # For example, you can check parts of the path construction:
            args, _ = mock_join.call_args
            assert "prompts" in args[0] # Check if 'prompts' is part of the path
            assert "prompt.md" in args[1]  # Check if 'prompt.md' is part of the path


def test_load_agent_prompt_file_not_found():
    with patch('os.path.join', return_value='dummy/path/to/nonexistent_prompt.md'):
        with patch('builtins.open', mock_open(read_data="")) as mock_file:
            mock_file.side_effect = FileNotFoundError("File not found")
            with pytest.raises(FileNotFoundError):
                load_agent_prompt()

@pytest.mark.asyncio
@patch('agent.agent.MCPToolset')
@patch('agent.agent.Agent')
@patch('agent.agent.Runner')
@patch('agent.agent.load_agent_prompt', return_value="Test Prompt")
async def test_initialize_agent_and_runner(mock_load_prompt, mock_runner_cls, mock_agent_cls, mock_mcp_toolset_cls):
    mock_mcp_instance = MagicMock(spec=MCPToolset)
    mock_mcp_toolset_cls.return_value = mock_mcp_instance
    
    mock_agent_instance = MagicMock()
    mock_agent_cls.return_value = mock_agent_instance
    
    mock_runner_instance = MagicMock()
    mock_runner_cls.return_value = mock_runner_instance

    runner, agent = await initialize_agent_and_runner()

    assert runner == mock_runner_instance
    assert agent == mock_agent_instance

    mock_mcp_toolset_cls.assert_called_once()
    # Check that SseServerParams was called with the correct URL
    args, kwargs = mock_mcp_toolset_cls.call_args
    assert 'connection_params' in kwargs
    assert isinstance(kwargs['connection_params'], SseServerParams)
    assert kwargs['connection_params'].url == VALID_MCP_URL
    
    mock_load_prompt.assert_called_once()
    
    mock_agent_cls.assert_called_once()
    agent_args, agent_kwargs = mock_agent_cls.call_args
    assert agent_kwargs['model'] == "gemini-test-model"
    assert agent_kwargs['name'] == APP_NAME
    assert agent_kwargs['instruction'] == "Test Prompt"
    # Check that MCPToolset instance is in the tools list
    assert mock_mcp_instance in agent_kwargs['tools']
    # Check that other tools are also present by their function names
    # (crontab_tool.schedule_task, etc.)
    tool_names = [t.__name__ if callable(t) else type(t).__name__ for t in agent_kwargs['tools']]
    assert 'schedule_task' in tool_names
    assert 'remove_task' in tool_names
    assert 'list_tasks' in tool_names
    assert 'get_current_time' in tool_names


    mock_runner_cls.assert_called_once_with(
        agent=mock_agent_instance,
        app_name=APP_NAME,
        session_service=mock_runner_cls.call_args.kwargs['session_service'] # session_service is instantiated internally
    )


@pytest.mark.asyncio
@patch('agent.agent.session_service', new_callable=AsyncMock) # Mock the session service
async def test_call_agent_async_new_session(mock_session_service):
    mock_runner = AsyncMock() # Use AsyncMock for the runner
    mock_session = AsyncMock()
    
    # Configure session_service mocks
    mock_session_service.get_session.return_value = None # Simulate no existing session
    mock_session_service.create_session.return_value = mock_session
    mock_session_service.append_event.return_value = None

    query = "Hello agent"
    user_id = "test_user"
    session_id = "test_session"

    # Mock the runner's run_async to be an async generator
    async def mock_run_async_gen(*args, **kwargs):
        # Yield a partial event and then a final event
        partial_event_content = genai_types.Content(role='model', parts=[genai_types.Part(text="Partial response")])
        yield Event(author="model", content=partial_event_content, partial=True)
        
        final_event_content = genai_types.Content(role='model', parts=[genai_types.Part(text="Final Answer")])
        yield Event(author="model", content=final_event_content, final=True)

    mock_runner.run_async.side_effect = mock_run_async_gen

    response = await call_agent_async(query, mock_runner, user_id, session_id)

    assert response == "Final Answer"
    mock_session_service.get_session.assert_called_once_with(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    mock_session_service.create_session.assert_called_once_with(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    
    # Check that append_event was called to update user_id in session state
    mock_session_service.append_event.assert_called_once()
    appended_event_arg = mock_session_service.append_event.call_args[0][1]
    assert isinstance(appended_event_arg, Event)
    assert appended_event_arg.author == "system"
    assert appended_event_arg.actions.state_delta == {"user_id": user_id}

    mock_runner.run_async.assert_called_once()
    run_async_args_kwargs = mock_runner.run_async.call_args.kwargs
    assert run_async_args_kwargs['user_id'] == user_id
    assert run_async_args_kwargs['session_id'] == session_id
    assert run_async_args_kwargs['new_message'].parts[0].text == query


@pytest.mark.asyncio
@patch('agent.agent.session_service', new_callable=AsyncMock)
async def test_call_agent_async_existing_session(mock_session_service):
    mock_runner = AsyncMock()
    mock_session = AsyncMock()

    mock_session_service.get_session.return_value = mock_session # Simulate existing session
    mock_session_service.append_event.return_value = None


    query = "Another query"
    user_id = "test_user_existing"
    session_id = "test_session_existing"

    async def mock_run_async_gen(*args, **kwargs):
        final_event_content = genai_types.Content(role='model', parts=[genai_types.Part(text="Existing Session Answer")])
        yield Event(author="model", content=final_event_content, final=True)
    mock_runner.run_async.side_effect = mock_run_async_gen

    response = await call_agent_async(query, mock_runner, user_id, session_id)

    assert response == "Existing Session Answer"
    mock_session_service.get_session.assert_called_once_with(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    mock_session_service.create_session.assert_not_called() # Should not create new session
    mock_session_service.append_event.assert_called_once()


@pytest.mark.asyncio
@patch('agent.agent.session_service', new_callable=AsyncMock)
async def test_call_agent_async_escalation(mock_session_service):
    mock_runner = AsyncMock()
    mock_session = AsyncMock()
    mock_session_service.get_session.return_value = mock_session
    mock_session_service.append_event.return_value = None

    query = "Escalate this"
    user_id = "test_user_escalate"
    session_id = "test_session_escalate"

    async def mock_run_async_gen(*args, **kwargs):
        # Simulate an event that indicates an escalation
        escalate_action = EventActions(escalate=True)
        yield Event(author="agent", actions=escalate_action, error_message="Something went wrong", final=True)
    mock_runner.run_async.side_effect = mock_run_async_gen

    response = await call_agent_async(query, mock_runner, user_id, session_id)
    assert "Agent escalated: Something went wrong" in response
