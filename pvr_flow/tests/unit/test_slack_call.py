import pytest
from unittest.mock import patch, MagicMock
from pvr_flow.slack_call import main

@patch("pvr_flow.slack_call.call_slack")
def test_slack_call_success(mock_call_slack):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_call_slack.return_value = mock_resp

    in_data = {
        "alert_id": "123",
        "service": "test",
        "severity": "critical",
        "message": "test msg",
        "host": "localhost",
        "triggered_at": "now",
        "should_page": True,
        "channel": "#test"
    }

    result = main(in_data)
    assert result["ok"] is True
    assert result["attempts"] == 1
    assert result["alert_id"] == "123"

@patch("pvr_flow.slack_call.time.sleep")
def test_slack_call_failure(mock_sleep):
    in_data = {
        "alert_id": "123",
        "service": "test",
        "severity": "critical",
        "message": "test msg",
        "host": "localhost",
        "triggered_at": "now",
        "should_page": True,
        "channel": "#test"
    }

    result = main(in_data, should_fail=True)
    assert result["ok"] is False
    assert result["attempts"] == 3
    assert mock_sleep.call_count == 2

def test_slack_call_dry_run():
    in_data = {
        "alert_id": "123",
        "channel": "#test"
    }
    result = main(in_data, dry_run=True)
    assert result["dry_run"] is True
