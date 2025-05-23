# agent/crontab_tool.py
from crontab import CronTab
import shlex # For escaping shell arguments
import json # Still needed for schedule_task

WEBHOOK_URL = "http://localhost:80/webhook"
COMMENT_PREFIX = "AGENT_SCHEDULED_MSG:"

def schedule_task(cron_expression, message):
    if not WEBHOOK_URL:
        print("Error: WEBHOOK_URL not configured.")
        return False

    try:
        # Escape the message for the JSON payload
        json_payload = json.dumps({"message": message})

        # Construct the curl command
        # Use shlex.quote for each part of the command that is a distinct shell argument.
        command = f"curl -X POST -H {shlex.quote('Content-Type: application/json')} -d {shlex.quote(json_payload)} {shlex.quote(WEBHOOK_URL)}"

        cron = CronTab(user=True)
        job = cron.new(command=command, comment=f"{COMMENT_PREFIX}{message}")
        job.setall(cron_expression) # Set the schedule for the job
        
        if not job.is_valid():
            # Attempt to remove the invalid job if it was somehow partially added,
            # though cron.new() followed by cron.write() is atomic in intent.
            # For an invalid expression, it's unlikely to be written, but good practice.
            # However, python-crontab might not add it to its internal list if new() fails with bad expression.
            # More importantly, if job.is_valid() is false after setall(), we shouldn't write.
            print(f"Error: Invalid cron expression: {cron_expression}")
            # It's good practice to try to remove a job that failed validation if it was added to the cron object
            # but before being written to the system crontab.
            # However, if is_valid() is false, cron.write() for this job might fail or write an invalid line.
            # The safest is not to proceed with cron.write() for this job or the entire crontab if one job is invalid.
            # For now, we just return False. A more robust error handling might remove the specific job
            # from the cron object before a potential write of other jobs.
            return False
            
        cron.write()
        print(f"Scheduled: '{message}' with schedule: '{cron_expression}'")
        return True
    except FileNotFoundError: # This can happen if crontab command is not found
        print("Error: crontab command not found. Is cron installed and in PATH?")
        return False
    except Exception as e:
        print(f"Error scheduling task: {e}")
        return False

def remove_task(message_identifier):
    try:
        cron = CronTab(user=True)
        removed_count = 0
        # Iterate over a copy of the jobs list if modifying it
        for job in list(cron): 
            if job.comment == f"{COMMENT_PREFIX}{message_identifier}":
                cron.remove(job)
                removed_count += 1
        
        if removed_count > 0:
            cron.write()
            print(f"Successfully removed {removed_count} task(s) matching: '{message_identifier}'")
            return True
        else:
            print(f"No scheduled task found with message: '{message_identifier}'")
            return False
    except FileNotFoundError:
        print("Error: crontab command not found. Is cron installed and in PATH?")
        return False
    except Exception as e:
        print(f"Error removing task: {e}")
        return False

def list_tasks():
    try:
        cron = CronTab(user=True)
        scheduled_tasks = []
        task_number = 1
        
        for job in cron:
            if job.comment.startswith(COMMENT_PREFIX):
                message = job.comment[len(COMMENT_PREFIX):]
                cron_expression = job.slices.render()
                try:
                    # Get human-readable description
                    # May need specific version of python-crontab or croniter for job.description()
                    # If job.description() is problematic or not available,
                    # Fallback to just cron_expression
                    # For example, croniter library might be needed for job.schedule().get_next().isoformat()
                    # or a more detailed description.
                    # For now, let's assume job.description() works or we handle its absence.
                    try:
                        description = job.description(use_24hour_time_format=True, verbose=True)
                    except AttributeError: # Some versions might not have verbose
                        description = job.description(use_24hour_time_format=True)
                    except Exception: # Catch any other error from job.description
                        description = "N/A (could not generate description)"

                except Exception as e: # Fallback if description fails
                    description = f"N/A (error: {e})"

                task_info = f"{task_number}. Message: '{message}', Schedule: '{cron_expression}', When: '{description}'"
                scheduled_tasks.append(task_info)
                task_number += 1
        
        if not scheduled_tasks:
            print("No tasks scheduled by this agent.")
            return []
        else:
            print("Scheduled tasks:")
            for task_str in scheduled_tasks:
                print(task_str)
            return scheduled_tasks

    except FileNotFoundError:
        print("Error: crontab command not found. Is cron installed and in PATH?")
        return []
    except Exception as e:
        print(f"Error listing tasks: {e}")
        return []

if __name__ == '__main__':
    # For testing purposes
    print(f"Webhook URL: {WEBHOOK_URL}")
    
    # Example usage (uncomment to test, be careful with your crontab)
    if WEBHOOK_URL: # Only proceed if webhook_url is loaded
        test_cron_expr = "*/1 * * * *" # Every minute for testing
        test_message = "Test task for listing"
        
        print("\n--- Testing schedule_task ---")
        if schedule_task(test_cron_expr, test_message):
            print(f"Scheduled: '{test_message}'")
            
            print("\n--- Testing list_tasks (after schedule) ---")
            list_tasks()
            
            print("\n--- Testing remove_task ---")
            if remove_task(test_message):
                print(f"Removed: '{test_message}'")
            else:
                print(f"Could not remove or find task: '{test_message}'")
            
            print("\n--- Testing list_tasks (after remove) ---")
            list_tasks()
            
        else:
            print(f"Failed to schedule test task: '{test_message}'")
            # Still try to list tasks in case some other tasks exist
            print("\n--- Testing list_tasks (if schedule failed but to see existing) ---")
            list_tasks()
    else:
        print("\nSkipping crontab interaction tests because WEBHOOK_URL is not set.")
        # Still call list_tasks to see if any pre-existing tasks are there
        print("\n--- Listing existing tasks (even if WEBHOOK_URL is not set) ---")
        list_tasks()
