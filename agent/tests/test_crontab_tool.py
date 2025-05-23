import unittest
from unittest.mock import patch, MagicMock, call
import json
import sys
import os
import shlex # Import shlex for constructing expected command

# Add agent directory to sys.path to import crontab_tool
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import crontab_tool 

# Ensure COMMENT_PREFIX is available as it's used in tests
# WEBHOOK_URL is now taken directly from the crontab_tool module's hardcoded value.
COMMENT_PREFIX = crontab_tool.COMMENT_PREFIX

class TestCrontabTool(unittest.TestCase):

    def setUp(self):
        # This can be used if tests need to share mock jobs, but often individual tests set up their own.
        self.mock_jobs = []
        # Store original WEBHOOK_URL to restore it if a test modifies it
        self.original_webhook_url = crontab_tool.WEBHOOK_URL

    def tearDown(self):
        # Restore WEBHOOK_URL after each test if it was changed
        crontab_tool.WEBHOOK_URL = self.original_webhook_url

    @patch('crontab_tool.CronTab')
    def test_schedule_task_success(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        mock_job = MagicMock()
        mock_job.is_valid.return_value = True
        mock_cron_instance.new.return_value = mock_job

        test_expr = "0 0 * * *"
        test_msg = "Test message with spaces & special chars like ' or \" quotes"
        
        result = crontab_tool.schedule_task(test_expr, test_msg)
        self.assertTrue(result)
        MockCronTab.assert_called_once_with(user=True)
        
        # Expected command construction
        json_payload = json.dumps({"message": test_msg})
        # Construct expected command using shlex.quote, similar to actual function
        expected_command = f"curl -X POST -H {shlex.quote('Content-Type: application/json')} -d {shlex.quote(json_payload)} {shlex.quote(crontab_tool.WEBHOOK_URL)}"
        
        mock_cron_instance.new.assert_called_once_with(
            command=expected_command,
            comment=COMMENT_PREFIX + test_msg
        )
        mock_job.setall.assert_called_once_with(test_expr)
        mock_cron_instance.write.assert_called_once()

    @patch('crontab_tool.CronTab')
    def test_schedule_task_no_webhook_url(self, MockCronTab):
        crontab_tool.WEBHOOK_URL = None # Modify for this test
        result = crontab_tool.schedule_task("0 0 * * *", "Test")
        self.assertFalse(result)
        MockCronTab.assert_not_called()
        # WEBHOOK_URL is restored in tearDown

    @patch('crontab_tool.CronTab')
    def test_schedule_task_invalid_cron_expression(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        mock_job = MagicMock()
        mock_job.is_valid.return_value = False # Simulate invalid cron expression
        mock_cron_instance.new.return_value = mock_job

        test_expr = "invalid cron string"
        test_msg = "Test message"
        
        result = crontab_tool.schedule_task(test_expr, test_msg)
        self.assertFalse(result)
        MockCronTab.assert_called_once_with(user=True)
        mock_cron_instance.new.assert_called_once() # It will create a job object
        mock_job.setall.assert_called_once_with(test_expr) # Attempt to set schedule
        mock_job.is_valid.assert_called_once() # Check validity
        mock_cron_instance.write.assert_not_called() # Should not write if invalid

    @patch('crontab_tool.CronTab')
    def test_remove_task_success(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        
        job1_msg = "message to remove"
        job1 = MagicMock()
        job1.comment = COMMENT_PREFIX + job1_msg
        
        job2 = MagicMock()
        job2.comment = COMMENT_PREFIX + "another message"
        
        job3 = MagicMock()
        job3.comment = "UNRELATED_JOB_MSG:some other message"
            
        mock_cron_instance.__iter__.return_value = [job1, job2, job3]

        result = crontab_tool.remove_task(job1_msg)
        self.assertTrue(result)
        mock_cron_instance.remove.assert_called_once_with(job1)
        mock_cron_instance.write.assert_called_once()

    @patch('crontab_tool.CronTab')
    def test_remove_task_not_found(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        
        job1 = MagicMock()
        job1.comment = COMMENT_PREFIX + "message1"
        job2 = MagicMock()
        job2.comment = COMMENT_PREFIX + "another message"
            
        mock_cron_instance.__iter__.return_value = [job1, job2]

        result = crontab_tool.remove_task("non_existent_message")
        self.assertFalse(result)
        mock_cron_instance.remove.assert_not_called()
        mock_cron_instance.write.assert_not_called()

    @patch('crontab_tool.CronTab')
    def test_list_tasks_found(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
            
        job1 = MagicMock()
        job1.comment = COMMENT_PREFIX + "Task 1"
        job1.slices.render.return_value = "* * * * *"
        job1.description.return_value = "Every minute"
            
        job2 = MagicMock() # This job should be ignored
        job2.comment = "OTHER_PREFIX:Task 2" 

        job3 = MagicMock()
        job3.comment = COMMENT_PREFIX + "Task 3"
        job3.slices.render.return_value = "0 0 * * *"
        job3.description.return_value = "Midnight daily"

        mock_cron_instance.__iter__.return_value = [job1, job2, job3]

        expected_list = [
            f"1. Message: 'Task 1', Schedule: '* * * * *', When: 'Every minute'",
            f"2. Message: 'Task 3', Schedule: '0 0 * * *', When: 'Midnight daily'"
        ]
            
        with patch('builtins.print') as mock_print:
            result = crontab_tool.list_tasks()
            self.assertEqual(result, expected_list)
            # Check if "Scheduled tasks:" and each task string was printed
            expected_print_calls = [call("Scheduled tasks:")] + [call(task_str) for task_str in expected_list]
            mock_print.assert_has_calls(expected_print_calls, any_order=False)

    @patch('crontab_tool.CronTab')
    def test_list_tasks_no_tasks_found(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        mock_cron_instance.__iter__.return_value = [] # No jobs at all

        with patch('builtins.print') as mock_print:
            result = crontab_tool.list_tasks()
            self.assertEqual(result, [])
            mock_print.assert_any_call("No tasks scheduled by this agent.")

    @patch('crontab_tool.CronTab')
    def test_list_tasks_no_matching_tasks(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        job_other_prefix = MagicMock()
        job_other_prefix.comment = "OTHER_PREFIX:Some task"
        mock_cron_instance.__iter__.return_value = [job_other_prefix] # Only non-matching jobs

        with patch('builtins.print') as mock_print:
            result = crontab_tool.list_tasks()
            self.assertEqual(result, [])
            mock_print.assert_any_call("No tasks scheduled by this agent.")

    @patch('crontab_tool.CronTab')
    def test_list_tasks_job_description_error(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        
        job1 = MagicMock()
        job1.comment = COMMENT_PREFIX + "Task 1 with error"
        job1.slices.render.return_value = "0 12 * * *"
        # Simulate an error when job.description() is called
        job1.description.side_effect = Exception("Failed to get description") 
            
        mock_cron_instance.__iter__.return_value = [job1]

        expected_list = [
            f"1. Message: 'Task 1 with error', Schedule: '0 12 * * *', When: 'N/A (could not generate description)'"
        ]
            
        with patch('builtins.print') as mock_print:
            result = crontab_tool.list_tasks()
            self.assertEqual(result, expected_list)
            mock_print.assert_any_call(expected_list[0])

    @patch('crontab_tool.CronTab')
    def test_list_tasks_job_description_attribute_error_verbose(self, MockCronTab):
        mock_cron_instance = MockCronTab.return_value
        
        job1 = MagicMock()
        job1.comment = COMMENT_PREFIX + "Task AttrError"
        job1.slices.render.return_value = "0 10 * * *"
        # Simulate AttributeError for verbose, then succeed without verbose
        job1.description.side_effect = [AttributeError("verbose not an option"), "Fallback description"]
            
        mock_cron_instance.__iter__.return_value = [job1]

        expected_list = [
            f"1. Message: 'Task AttrError', Schedule: '0 10 * * *', When: 'Fallback description'"
        ]
            
        with patch('builtins.print') as mock_print:
            result = crontab_tool.list_tasks()
            self.assertEqual(result, expected_list)
            # Check that description was called twice (first with verbose, then without)
            self.assertEqual(job1.description.call_count, 2)
            job1.description.assert_has_calls([
                call(use_24hour_time_format=True, verbose=True),
                call(use_24hour_time_format=True)
            ])


if __name__ == '__main__':
    unittest.main()
