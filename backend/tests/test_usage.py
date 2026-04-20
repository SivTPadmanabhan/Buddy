import json
from datetime import date, timedelta

import pytest

from app.services.usage import UsageTracker


LIMITS = {"gemini_requests": 1000, "gemini_tokens": 500000, "pinecone_vectors": 80000}


def test_fresh_tracker_has_zero_usage(usage_file):
    t = UsageTracker(usage_file, LIMITS)
    status = t.get_usage_status()
    assert status["gemini_requests"]["used"] == 0
    assert status["gemini_requests"]["limit"] == 1000
    assert status["gemini_requests"]["percent"] == 0.0


def test_record_usage_increments_counter(usage_file):
    t = UsageTracker(usage_file, LIMITS)
    t.record_usage("gemini_requests", 3)
    t.record_usage("gemini_tokens", 1500)
    assert t.get_usage_status()["gemini_requests"]["used"] == 3
    assert t.get_usage_status()["gemini_tokens"]["used"] == 1500


def test_check_limit_allows_under(usage_file):
    t = UsageTracker(usage_file, LIMITS)
    t.record_usage("gemini_requests", 500)
    assert t.check_limit("gemini_requests", 100) is True


def test_check_limit_blocks_over(usage_file):
    t = UsageTracker(usage_file, LIMITS)
    t.record_usage("gemini_requests", 999)
    assert t.check_limit("gemini_requests", 2) is False


def test_persists_across_instances(usage_file):
    UsageTracker(usage_file, LIMITS).record_usage("gemini_tokens", 42)
    t2 = UsageTracker(usage_file, LIMITS)
    assert t2.get_usage_status()["gemini_tokens"]["used"] == 42


def test_resets_on_new_day(usage_file):
    t = UsageTracker(usage_file, LIMITS)
    t.record_usage("gemini_requests", 500)

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    data = json.loads(usage_file.read_text())
    data["date"] = yesterday
    usage_file.write_text(json.dumps(data))

    t2 = UsageTracker(usage_file, LIMITS)
    assert t2.get_usage_status()["gemini_requests"]["used"] == 0


def test_unknown_service_raises(usage_file):
    t = UsageTracker(usage_file, LIMITS)
    with pytest.raises(ValueError):
        t.record_usage("nonexistent", 1)
