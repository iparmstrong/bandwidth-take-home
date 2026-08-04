import pytest
from hypothesis import given, strategies as st
from pvr_flow.classify import main as classify_main

@given(
    st.dictionaries(st.text(), st.text()).map(lambda d: {**d, "severity": "critical"})
)
def test_classify_routing_critical(payload):
    result = classify_main(payload)
    assert result["should_page"] is True
    assert result["channel"] == "#incidents"
    for k, v in payload.items():
        if k not in ("should_page", "channel"):
            assert result[k] == v

@given(
    st.dictionaries(st.text(), st.text()).map(lambda d: {**d, "severity": "warning"})
)
def test_classify_routing_warning(payload):
    result = classify_main(payload)
    assert result["should_page"] is False
    assert result["channel"] == "#alerts"
    for k, v in payload.items():
        if k not in ("should_page", "channel"):
            assert result[k] == v

@given(
    st.dictionaries(st.text(), st.text()).map(lambda d: {**d, "severity": "info"})
)
def test_classify_routing_info(payload):
    result = classify_main(payload)
    assert result["should_page"] is False
    assert result["channel"] == "#monitoring"
    for k, v in payload.items():
        if k not in ("should_page", "channel"):
            assert result[k] == v
