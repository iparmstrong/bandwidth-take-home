import pytest
from pvr_flow.classify_script import main


def test_classify_critical():
    result = main({"severity": "critical", "other": "value"})
    assert result["should_page"] is True
    assert result["channel"] == "#incidents"
    assert result["severity"] == "critical"
    assert result["other"] == "value"


def test_classify_warning():
    result = main({"severity": "warning", "other": "value"})
    assert result["should_page"] is False
    assert result["channel"] == "#alerts"
    assert result["severity"] == "warning"
    assert result["other"] == "value"


def test_classify_info():
    result = main({"severity": "info", "other": "value"})
    assert result["should_page"] is False
    assert result["channel"] == "#monitoring"
    assert result["severity"] == "info"
    assert result["other"] == "value"
