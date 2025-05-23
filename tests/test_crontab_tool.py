import pytest
from unittest.mock import patch, MagicMock, call
from agent.tools.crontab_tool import (
    validate_webhook_url,
    schedule_task,
    remove_task,
    list_tasks,
    COMMENT_PREFIX,
    QUERY_PREFIX
)
from google.adk.tools import ToolContext

# Define a constant for a valid webhook URL for testing
VALID_WEBHOOK_URL = "http://localhost:8080/webhook"
# Define a constant for an invalid webhook URL for testing
INVALID_WEBHOOK_URL = "htp:/localhost"

@pytest.fixture
def mock_tool_context(monkeypatch):
    context = MagicMock(spec=ToolContext)
    context.state = {"user_id": "test_user_123"}
    return context

@pytest.fixture(autouse=True)
def set_webhook_url(monkeypatch):
    monkeypatch.setenv("WHATSAPP_WEBHOOK_URL", VALID_WEBHOOK_URL)
    # Ensure QUERY_PREFIX has a default for tests if not set elsewhere
    monkeypatch.setenv("QUERY_PREFIX", "/query ")


@pytest.mark.parametrize("url, expected", [
    ("http://valid.com/path", True),
    ("https://valid.com", True),
    ("ftp://valid.com", True), # scheme can be other things too
    ("http://localhost:8000", True),
    ("invalid-url", False),
    ("http:/missing-slash.com", False),
    ("http//missing-colon.com", False),
    ("", False),
    (None, False)
])
def test_validate_webhook_url(url, expected):
    assert validate_webhook_url(url) == expected

@patch('agent.tools.crontab_tool.CronTab')
def test_schedule_task_success(mock_crontab_cls, mock_tool_context):
    mock_cron_instance = MagicMock()
    mock_job = MagicMock()
    mock_job.is_valid.return_value = True
    mock_cron_instance.new.return_value = mock_job
    mock_crontab_cls.return_value = mock_cron_instance

    cron_expr = "0 0 * * *"
    message = "Test message"
    
    result = schedule_task(cron_expr, message, mock_tool_context)

    assert result["status"] == "success"
    assert result["result"] is True
    mock_crontab_cls.assert_called_once_with(user=True)
    
    expected_user_id = "test_user_123"
    expected_json_payload = f'{{"name": "My past self", "from": "{expected_user_id}", "message": "{QUERY_PREFIX}{message}"}}'
    expected_command = f"curl -X POST -H 'Content-Type: application/json' -d '{expected_json_payload}' '{VALID_WEBHOOK_URL}'"
    
    mock_cron_instance.new.assert_called_once_with(command=expected_command, comment=f"{COMMENT_PREFIX}{message}")
    mock_job.setall.assert_called_once_with(cron_expr)
    mock_job.is_valid.assert_called_once()
    mock_cron_instance.write.assert_called_once()

@patch('agent.tools.crontab_tool.CronTab')
def test_schedule_task_invalid_cron_expression(mock_crontab_cls, mock_tool_context):
    mock_cron_instance = MagicMock()
    mock_job = MagicMock()
    mock_job.is_valid.return_value = False # Simulate invalid cron expression
    mock_cron_instance.new.return_value = mock_job
    mock_crontab_cls.return_value = mock_cron_instance

    result = schedule_task("invalid cron", "Test", mock_tool_context)
    assert result["status"] == "error"
    assert result["result"] is False
    assert "Invalid cron expression" in result["error_message"]
    mock_cron_instance.write.assert_not_called()

@patch('agent.tools.crontab_tool.CronTab')
def test_schedule_task_no_user_id(mock_crontab_cls, mock_tool_context):
    mock_tool_context.state = {} # Simulate missing user_id
    result = schedule_task("0 0 * * *", "Test", mock_tool_context)
    assert result["status"] == "error"
    assert result["result"] is False
    assert "User ID not found" in result["error_message"]
    mock_crontab_cls.return_value.write.assert_not_called()


def test_schedule_task_invalid_webhook_url(monkeypatch, mock_tool_context):
    monkeypatch.setenv("WHATSAPP_WEBHOOK_URL", INVALID_WEBHOOK_URL)
    result = schedule_task("0 0 * * *", "Test", mock_tool_context)
    assert result["status"] == "error"
    assert result["result"] is False
    assert f"Invalid webhook URL: {INVALID_WEBHOOK_URL}" in result["error_message"]

@patch('agent.tools.crontab_tool.CronTab')
def test_schedule_task_message_too_long(mock_crontab_cls, mock_tool_context):
    long_message = "a" * 1001
    result = schedule_task("0 0 * * *", long_message, mock_tool_context)
    assert result["status"] == "error"
    assert result["result"] is False
    assert "Message is empty or too long" in result["error_message"]
    mock_crontab_cls.return_value.write.assert_not_called()

@patch('agent.tools.crontab_tool.CronTab')
def test_schedule_task_crontab_not_found(mock_crontab_cls, mock_tool_context):
    mock_crontab_cls.side_effect = FileNotFoundError("Crontab not found")
    result = schedule_task("0 0 * * *", "Test", mock_tool_context)
    assert result["status"] == "error"
    assert result["result"] is False
    assert "Crontab command not found" in result["error_message"]

@patch('agent.tools.crontab_tool.CronTab')
def test_remove_task_success(mock_crontab_cls):
    mock_cron_instance = MagicMock()
    mock_job1 = MagicMock()
    mock_job1.comment = f"{COMMENT_PREFIX}Task to remove"
    mock_job2 = MagicMock()
    mock_job2.comment = "Other task"
    mock_cron_instance.__iter__.return_value = [mock_job1, mock_job2] # Make it iterable
    mock_crontab_cls.return_value = mock_cron_instance

    result = remove_task("Task to remove")
    assert result["status"] == "success"
    assert result["result"] is True
    mock_cron_instance.remove.assert_called_once_with(mock_job1)
    mock_cron_instance.write.assert_called_once()

@patch('agent.tools.crontab_tool.CronTab')
def test_remove_task_not_found(mock_crontab_cls):
    mock_cron_instance = MagicMock()
    mock_job = MagicMock()
    mock_job.comment = "Some other task"
    mock_cron_instance.__iter__.return_value = [mock_job]
    mock_crontab_cls.return_value = mock_cron_instance

    result = remove_task("NonExistentTask")
    assert result["status"] == "success" # The function itself succeeds
    assert result["result"] is False      # But reports no task was found/removed
    assert result["error_message"] is None
    mock_cron_instance.remove.assert_not_called()
    mock_cron_instance.write.assert_not_called() # Write is not called if nothing is removed

def test_remove_task_empty_identifier():
    result = remove_task("")
    assert result["status"] == "error"
    assert result["result"] is False
    assert "Message identifier cannot be empty" in result["error_message"]


@patch('agent.tools.crontab_tool.CronTab')
def test_remove_task_crontab_not_found(mock_crontab_cls):
    mock_crontab_cls.side_effect = FileNotFoundError("Crontab not found")
    result = remove_task("any_task")
    assert result["status"] == "error"
    assert result["result"] is False
    assert "Crontab command not found" in result["error_message"]


@patch('agent.tools.crontab_tool.CronTab')
def test_list_tasks_success(mock_crontab_cls):
    mock_cron_instance = MagicMock()
    mock_job1 = MagicMock()
    mock_job1.comment = f"{COMMENT_PREFIX}First task"
    mock_job1.slices.render.return_value = "* * * * *"
    mock_job1.description.return_value = "Runs every minute"

    mock_job2 = MagicMock()
    mock_job2.comment = f"{COMMENT_PREFIX}Second task"
    mock_job2.slices.render.return_value = "0 0 * * *"
    mock_job2.description.return_value = "Runs daily at midnight"
    
    mock_job_other_agent = MagicMock() # A job not scheduled by this agent
    mock_job_other_agent.comment = "SOME_OTHER_AGENT:Other task"
    mock_job_other_agent.slices.render.return_value = "0 1 * * *"
    mock_job_other_agent.description.return_value = "Runs daily at 1 AM"


    mock_cron_instance.__iter__.return_value = [mock_job1, mock_job_other_agent, mock_job2]
    mock_crontab_cls.return_value = mock_cron_instance

    result = list_tasks()
    assert result["status"] == "success"
    assert len(result["result"]) == 2
    assert "1. Message: 'First task', Schedule: '* * * * *', When: 'Runs every minute'" in result["result"][0]
    assert "2. Message: 'Second task', Schedule: '0 0 * * *', When: 'Runs daily at midnight'" in result["result"][1]
    
    # Ensure job.description was called with the correct arguments
    # Check calls for description method, which might be called with different args based on crontab version
    expected_calls_job1 = [
        call(use_24hour_time_format=True, verbose=True),
        call(use_24hour_time_format=True) # Fallback call
    ]
    # We can't easily assert just one of these was called without more complex mocking,
    # so we check if at least the primary attempt was made.
    assert any(c == expected_calls_job1[0] for c in mock_job1.description.call_args_list) or \
           any(c == expected_calls_job1[1] for c in mock_job1.description.call_args_list)


@patch('agent.tools.crontab_tool.CronTab')
def test_list_tasks_no_agent_tasks(mock_crontab_cls):
    mock_cron_instance = MagicMock()
    mock_job_other_agent = MagicMock() 
    mock_job_other_agent.comment = "SOME_OTHER_AGENT:Other task"
    mock_cron_instance.__iter__.return_value = [mock_job_other_agent] # Only tasks from other agents
    mock_crontab_cls.return_value = mock_cron_instance

    result = list_tasks()
    assert result["status"] == "success"
    assert result["result"] == [] # Should be an empty list

@patch('agent.tools.crontab_tool.CronTab')
def test_list_tasks_empty_crontab(mock_crontab_cls):
    mock_cron_instance = MagicMock()
    mock_cron_instance.__iter__.return_value = [] # Empty crontab
    mock_crontab_cls.return_value = mock_cron_instance

    result = list_tasks()
    assert result["status"] == "success"
    assert result["result"] == []


@patch('agent.tools.crontab_tool.CronTab')
def test_list_tasks_crontab_not_found(mock_crontab_cls):
    mock_crontab_cls.side_effect = FileNotFoundError("Crontab not found")
    result = list_tasks()
    assert result["status"] == "error"
    assert result["result"] == []
    assert "Crontab command not found" in result["error_message"]

@patch('agent.tools.crontab_tool.CronTab')
def test_list_tasks_description_error(mock_crontab_cls):
    mock_cron_instance = MagicMock()
    mock_job1 = MagicMock()
    mock_job1.comment = f"{COMMENT_PREFIX}Task with error"
    mock_job1.slices.render.return_value = "* * * * *"
    # Simulate an error during description generation
    mock_job1.description.side_effect = Exception("Description generation failed")
    
    mock_cron_instance.__iter__.return_value = [mock_job1]
    mock_crontab_cls.return_value = mock_cron_instance

    result = list_tasks()
    assert result["status"] == "success" # The function itself succeeds
    assert len(result["result"]) == 1
    assert "Message: 'Task with error'" in result["result"][0]
    assert "When: 'N/A (error: Description generation failed)'" in result["result"][0]
