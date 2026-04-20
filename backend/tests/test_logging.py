import json
import logging

from app.logging_config import configure_logging, get_logger


def test_logger_emits_json(env, capsys):
    configure_logging()
    log = get_logger("test")
    log.info("event_happened", category="system", action="startup", foo="bar")
    out = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(out)
    assert payload["event"] == "event_happened"
    assert payload["category"] == "system"
    assert payload["action"] == "startup"
    assert payload["foo"] == "bar"
    assert payload["level"] == "info"
