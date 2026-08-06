import pytest
from hypothesis import given, settings, strategies as st
from pvr_flow.slack_call import main as slack_call_main


@given(
    st.fixed_dictionaries(
        {
            "alert_id": st.text(),
            "channel": st.text(),
            "service": st.text(),
            "message": st.text(),
            "host": st.text(),
            "triggered_at": st.text(),
            "should_page": st.booleans(),
        }
    ),
    st.booleans(),  # dry_run
    st.booleans(),  # should_fail
)
@settings(deadline=None, max_examples=5)
def test_slack_call(in_data, dry_run, should_fail):
    result = slack_call_main(in_data, dry_run=dry_run, should_fail=should_fail)

    assert result["alert_id"] == in_data.get("alert_id")
    assert result["channel"] == in_data.get("channel")
    assert result["dry_run"] == dry_run

    if should_fail:
        assert result["ok"] is False
        assert result["attempts"] == 3  # max_attempts
    else:
        assert result["ok"] is True
        assert result["attempts"] == 1
