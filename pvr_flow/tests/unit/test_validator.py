import pytest
from pvr_flow.validator import main

def test_valid_payload():
    payload = {
        "alert_id": "ALT-4892",
        "service": "payments-api",
        "severity": "critical",
        "message": "HTTP 5xx error rate exceeded",
        "host": "prod-payments-01",
        "triggered_at": 1742046720,
    }
    result = main(payload)
    assert result.get("valid") is not False
    assert result["alert_id"] == "ALT-4892"
    assert result["triggered_at"].endswith("Z")
    assert result["dry_run"] is False

def test_invalid_severity():
    payload = {
        "alert_id": "ALT-1",
        "service": "test",
        "severity": "unknown",
        "message": "test",
        "host": "test",
        "triggered_at": 1742046720,
    }
    result = main(payload)
    assert result.get("valid") is not False
    assert result["severity"] == "info"

def test_missing_fields():
    payload = {
        "service": "test"
    }
    result = main(payload)
    assert result.get("valid") is False
    assert result.get("error") == "validation_failed"

def test_dry_run():
    payload = {
        "alert_id": "ALT-4892",
        "service": "payments-api",
        "severity": "critical",
        "message": "msg",
        "host": "host",
        "triggered_at": 1742046720,
    }
    result = main(payload, dry_run=True)
    assert result["dry_run"] is True

def test_already_iso_date():
    payload = {
        "alert_id": "ALT-4892",
        "service": "payments-api",
        "severity": "critical",
        "message": "msg",
        "host": "host",
        "triggered_at": "2026-08-04T12:00:00Z",
    }
    result = main(payload)
    assert result["triggered_at"] == "2026-08-04T12:00:00Z"
