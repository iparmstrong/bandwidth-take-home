# test: script/u/admin/parse_alert
import wmill
from typing import Any
import re


VALID_PAYLOAD = {
    "alert_id": "ALT-4892",
    "service": "payments-api",
    "severity": "critical",
    "message": "HTTP 5xx error rate exceeded 5% over a 5-minute window",
    "host": "prod-payments-01",
    "triggered_at": 1742046720,
}

def validate_result(payload: dict[str,str | int], result: dict[str, Any]):
    res_alert_id = result.get("alert_id")
    res_service = result.get("service")
    res_severity = result.get("severity")
    res_message = result.get("message")
    res_host = result.get("host")
    res_triggered_at = result.get("triggered_at")
    source_alert_id = payload.get("alert_id")
    source_service = payload.get("service")
    source_severity = payload.get("severity")
    source_message = payload.get("message")
    source_host = payload.get("host")

    assert res_alert_id == source_alert_id, f"Expected alert_id {source_alert_id}, got {res_alert_id}"
    assert res_service == source_service, f"Expected service {source_service}, got {res_service}"
    assert res_severity == source_severity, f"Expected severity {source_severity}, got {res_severity}"
    assert res_message == source_message, f"Expected message {source_message}, got {res_message}"
    assert res_host == source_host, f"Expected host {source_host}, got {res_host}"
    assert isinstance(res_triggered_at, str), f"Expected string triggered_at, got {type(res_triggered_at)}"
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", res_triggered_at), f"Expected triggered_at to match UTC ISO-8601 regex, got {res_triggered_at}"
    assert result.get("dry_run") is True, f"Expected dry_run to be True, got {result.get('dry_run')}"

def main():
    print("Starting tests for u/admin/parse_alert...")
    
    # Call u/admin/parse_alert via wmill.run_script with VALID_PAYLOAD
    # and dry_run=True, and assert the output looks the way you expect.
    print("Running test: Valid payload")
    result = wmill.run_script_by_path("u/admin/parse_alert", {"payload": VALID_PAYLOAD, "dry_run": True})
    validate_result(VALID_PAYLOAD, result)
    print("Passed: Valid payload")

    # Exercise at least one malformed-input case and assert your
    # Problem 1 script handles it the way you designed it to.
    
    # Malformed Case 1: Missing required field (alert_id)
    print("Running test: Malformed Case 1 - Missing alert_id")
    payload_missing_id = VALID_PAYLOAD.copy()
    del payload_missing_id["alert_id"]
    result_missing_id = wmill.run_script_by_path("u/admin/parse_alert", {"payload": payload_missing_id, "dry_run": True})
    assert result_missing_id.get("valid") is False, "Expected False for missing alert_id"
    assert result_missing_id.get("error") == "validation_failed"
    print("Passed: Malformed Case 1")

    # Malformed Case 2: Empty alert_id (violates min_length=1)
    print("Running test: Malformed Case 2 - Empty alert_id")
    payload_empty_id = VALID_PAYLOAD.copy()
    payload_empty_id["alert_id"] = ""
    result_empty_id = wmill.run_script_by_path("u/admin/parse_alert", {"payload": payload_empty_id, "dry_run": True})
    assert result_empty_id.get("valid") is False, "Expected False for empty alert_id"
    assert result_empty_id.get("error") == "validation_failed"
    print("Passed: Malformed Case 2")

    # Malformed Case 3: Missing service
    print("Running test: Malformed Case 3 - Missing service")
    payload_missing_service = VALID_PAYLOAD.copy()
    del payload_missing_service["service"]
    result_missing_service = wmill.run_script_by_path("u/admin/parse_alert", {"payload": payload_missing_service, "dry_run": True})
    assert result_missing_service.get("valid") is False, "Expected False for missing service"
    assert result_missing_service.get("error") == "validation_failed"
    print("Passed: Malformed Case 3")
    
    # Edge Case: Unrecognized severity (gracefully degrades to 'info')
    print("Running test: Edge Case - Unrecognized severity")
    payload_invalid_severity = VALID_PAYLOAD.copy()
    payload_invalid_severity["severity"] = "unknown_severity"
    result_invalid_severity = wmill.run_script_by_path("u/admin/parse_alert", {"payload": payload_invalid_severity, "dry_run": True})
    assert result_invalid_severity.get("severity") == "info", f"Expected 'info', got {result_invalid_severity.get('severity')}"
    print("Passed: Edge Case - Unrecognized severity")
    
    print("All tests passed successfully!")
    return "All tests passed!"