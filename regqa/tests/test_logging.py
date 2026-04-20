import json
import logging

from regqa.logging import JsonFormatter


def _record(**extra) -> logging.LogRecord:
    record = logging.LogRecord("t", logging.INFO, "f.py", 1, "fetch_complete", None, None)
    record.__dict__.update(extra)
    return record


def test_extra_fields_reach_the_payload():
    payload = json.loads(JsonFormatter().format(_record(doc_id=41, ms=812)))
    assert payload["event"] == "fetch_complete"
    assert payload["level"] == "INFO"
    assert payload["doc_id"] == 41
    assert payload["ms"] == 812


def test_standard_attributes_are_not_duplicated():
    payload = json.loads(JsonFormatter().format(_record()))
    assert "msg" not in payload
    assert "lineno" not in payload
