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
        "channel": "#test",
    }

    result = main(in_data)
    assert result["ok"] is True
    assert result["attempts"] == 1
    assert result["alert_id"] == "123"


@patch("pvr_flow.slack_call.time.sleep")
@patch("pvr_flow.slack_call.call_slack")
def test_slack_call_failure(mock_call_slack, mock_sleep):
    import httpx

    # Simulate a 503 error on all attempts
    req = httpx.Request("POST", "https://slack.com")
    mock_call_slack.return_value = httpx.Response(503, request=req)

    in_data = {
        "alert_id": "123",
        "service": "test",
        "severity": "critical",
        "message": "test msg",
        "host": "localhost",
        "triggered_at": "now",
        "should_page": True,
        "channel": "#test",
    }

    # Call main without the should_fail flag
    result = main(in_data)

    assert result["ok"] is False
    assert result["attempts"] == 3
    assert mock_sleep.call_count == 2


@patch("pvr_flow.slack_call.time.sleep")
@patch("pvr_flow.slack_call.call_slack")
def test_slack_call_eventual_success(mock_call_slack, mock_sleep):
    import httpx

    # Simulate a 503 error on first two attempts, then 200 success
    req = httpx.Request("POST", "https://slack.com")
    mock_call_slack.side_effect = [
        httpx.Response(503, request=req),
        httpx.Response(503, request=req),
        httpx.Response(200, request=req),
    ]

    in_data = {
        "alert_id": "123",
        "service": "test",
        "severity": "critical",
        "message": "test msg",
        "host": "localhost",
        "triggered_at": "now",
        "should_page": True,
        "channel": "#test",
    }

    result = main(in_data)

    assert result["ok"] is True
    assert result["attempts"] == 3
    assert mock_sleep.call_count == 2
    assert mock_call_slack.call_count == 3


@patch("pvr_flow.slack_call.time.sleep")
@patch("pvr_flow.slack_call.call_slack")
def test_slack_call_extra_fields(mock_call_slack, mock_sleep):
    import httpx

    # Simulate a 503 error on all attempts
    req = httpx.Request("POST", "https://slack.com")
    mock_call_slack.return_value = httpx.Response(200, request=req)

    in_data = {
        "alert_id": "123",
        "service": "test",
        "severity": "critical",
        "message": "test msg",
        "host": "localhost",
        "triggered_at": "now",
        "should_page": True,
        "channel": "#test",
        "probable_cause": "AI output probable cause",
        "summary": "AI output probable cause",
    }

    # Call main without the should_fail flag
    result = main(in_data)

    assert result["ok"] is True
    assert result["attempts"] == 1
    assert mock_sleep.call_count == 0
    assert result["alert_id"] == "123"


def test_slack_call_dry_run():
    in_data = {"alert_id": "123", "channel": "#test"}
    result = main(in_data, dry_run=True)
    assert result["dry_run"] is True
