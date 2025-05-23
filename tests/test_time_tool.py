import pytest
from datetime import datetime
from agent.tools.time_tool import get_current_time

def test_get_current_time_success():
    """Test that get_current_time returns the correct structure and types."""
    result = get_current_time()

    assert result["status"] == "success"
    assert result["error_message"] is None
    assert isinstance(result["result"], dict)

    time_data = result["result"]
    now = datetime.now()

    assert "datetime" in time_data
    assert "date" in time_data
    assert "time" in time_data
    assert "hour" in time_data
    assert "minute" in time_data
    assert "day" in time_data
    assert "month" in time_data
    assert "year" in time_data
    assert "weekday" in time_data

    # Check if the format of datetime, date, and time strings are correct
    try:
        datetime.strptime(time_data["datetime"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pytest.fail("Incorrect datetime format")

    try:
        datetime.strptime(time_data["date"], "%Y-%m-%d")
    except ValueError:
        pytest.fail("Incorrect date format")

    try:
        datetime.strptime(time_data["time"], "%H:%M:%S")
    except ValueError:
        pytest.fail("Incorrect time format")

    # Check if numeric values are of correct type and within reasonable ranges
    assert isinstance(time_data["hour"], int)
    assert 0 <= time_data["hour"] <= 23
    assert isinstance(time_data["minute"], int)
    assert 0 <= time_data["minute"] <= 59
    assert isinstance(time_data["day"], int)
    assert 1 <= time_data["day"] <= 31
    assert isinstance(time_data["month"], int)
    assert 1 <= time_data["month"] <= 12
    assert isinstance(time_data["year"], int)
    assert time_data["year"] == now.year  # Year should match current year
    assert isinstance(time_data["weekday"], int)
    assert 0 <= time_data["weekday"] <= 6

    # Check consistency (e.g., date parts match datetime string)
    parsed_datetime = datetime.strptime(time_data["datetime"], "%Y-%m-%d %H:%M:%S")
    assert parsed_datetime.year == time_data["year"]
    assert parsed_datetime.month == time_data["month"]
    assert parsed_datetime.day == time_data["day"]
    assert parsed_datetime.hour == time_data["hour"]
    assert parsed_datetime.minute == time_data["minute"]

    # It's hard to test exact second, so we check if it's close
    assert abs(parsed_datetime.second - now.second) <= 1
