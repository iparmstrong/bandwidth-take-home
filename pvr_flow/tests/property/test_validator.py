import pytest
from hypothesis import given, strategies as st
from pvr_flow.parse_alert import main as validator_main
import re


@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.sampled_from(["critical", "warning", "info"]),
    st.text(),
    st.text(),
    st.integers(min_value=0, max_value=2000000000),
)
def test_validator_valid_payload(
    alert_id, service, severity, message, host, triggered_at
):
    payload = {
        "alert_id": alert_id,
        "service": service,
        "severity": severity,
        "message": message,
        "host": host,
        "triggered_at": triggered_at,
    }
    result = validator_main(payload)

    # Must be valid
    assert result.get("valid") is not False
    assert result["alert_id"] == alert_id
    assert result["service"] == service
    assert result["severity"] == severity
    assert result["message"] == message
    assert result["host"] == host

    # triggered_at check
    assert isinstance(result["triggered_at"], str)
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", result["triggered_at"])


@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.text().filter(lambda x: x not in ["critical", "warning", "info"]),
    st.text(),
    st.text(),
    st.integers(min_value=0, max_value=2000000000),
)
def test_validator_invalid_severity(
    alert_id, service, severity, message, host, triggered_at
):
    payload = {
        "alert_id": alert_id,
        "service": service,
        "severity": severity,
        "message": message,
        "host": host,
        "triggered_at": triggered_at,
    }
    result = validator_main(payload)

    # Invalid severity should be downgraded to "info"
    assert result.get("valid") is not False
    assert result["severity"] == "unknown"


@given(
    st.fixed_dictionaries(
        {
            "alert_id": st.text(min_size=1),
            "service": st.text(min_size=1),
            "severity": st.sampled_from(["critical", "warning", "info"]),
            "message": st.text(),
            "host": st.text(),
            "triggered_at": st.integers(min_value=0, max_value=2000000000),
        }
    ),
    st.sampled_from(["alert_id", "service", "message", "host", "triggered_at"]),
)
def test_validator_missing_required_fields(payload, missing_field):
    # Remove one required field
    del payload[missing_field]

    result = validator_main(payload)
    assert result.get("valid") is False
    assert result.get("error") == "validation_failed"
