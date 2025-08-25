
from adapters.c14_adapter import adapt_records
from adapters.c14_adapter import parse_hebrew_time_label, is_time_label
import pytest
from datetime import datetime, timedelta, timezone

# Mini cheat‑sheet
    # Define: @pytest.fixture function → returns or yields something.
    # Use: add the fixture name as a function parameter in your test.
    # Clean up: put cleanup after yield.
    # Share: place in tests/conftest.py.

@pytest.fixture
def base_now():
    # Fixed base time for tests: 2025-08-24T15:41:39+03:00
    return datetime.fromisoformat("2025-08-24T15:41:39+03:00")

def test_adapter_sets_published_iso_when_time_label(base_now):
    rec = {
        "title": "כותרת",
        "published": "לפני שעה",
        "scraped_at": base_now.isoformat(timespec="seconds"),
        "url": "https://C14.co.il/article/128?utm_source=x#frag"
    }
    out = adapt_records([rec])[0]
    assert out["published_iso"].endswith("+03:00") or out["published_iso"].endswith("+02:00")
    assert out["published_iso"] is not None

import json
import pytest

def test_is_time_label_positive():
    # cases = [
    #     "לפני שעה", "לפני 3 שעות", "לפני דקה", "לפני 2 ימים", "לפני יום",
    #     "לפני 5 דקות", "לפני 10 ימים", "אתמול", "לפני כשעה", "לפני 4 דק'",
    #     "לפני 5 דקות", "לפני שעתיים", "לפני 3 שעות", "21.08.25",
    #      "אתמול 23:30", "00:09",
        
    # ]

    # bad = ['הולנדר: "הניסיון שלי זה החיים שאחרי - לא מובן מאליו"',"הצהרת תובע הוגשה כנגד אחד החשודים",]       # should automate the outputs of the bad list into adapt_records func (c14_adapter.py)
    
    cases = [
    "לפני שעתיים",
    "לפני 55 דקות",
    "לפני 25 דקות",
    "לפני 3 שעות",
    "לפני שעתיים",
    "לפני כשעה",
    "לפני 38 דקות",
    "לפני 3 שעות",
    "לפני 3 שעות",
    "לפני 43 דקות",
    "לפני שעתיים",
    "לפני כשעה",
    "לפני שעתיים",
    "05:58",
    "אתמול 20:25",
    "אתמול 19:43",
    "אתמול 21:20",
    "אתמול 18:40",
    "אתמול 16:34",
    "אתמול 14:21",
    "לפני 3 שעות",
    "00:16",
    "אתמול 20:07",
    "אתמול 20:04",
    "לפני 3 שעות",
    "לפני 3 שעות",
    "לפני 3 שעות",
    "לפני 3 שעות",
    "לפני 3 שעות",
    "לפני 3 שעות",
    "אתמול 20:41",
    "אתמול 18:06",
    "אתמול 17:57",
    "לפני כשעה",
    "לפני כשעה",
    "לפני כשעה",
    "לפני כשעה",
    "לפני כשעה",
    "לפני כשעה",
    "לפני שעתיים",
    "לפני 3 שעות",
    "לפני 3 שעות",
]
    bad = []
    errors = []

    for s in cases:
        try:
            if is_time_label(s) is not True:
                bad.append(s)
        except Exception as e:
            errors.append({"value": s, "error": repr(e)})

    msg_parts = []
    if bad:
        msg_parts.append("Returned False for:\n" + json.dumps(bad, ensure_ascii=False, indent=2))
    if errors:
        msg_parts.append("Raised exceptions for:\n" + json.dumps(errors, ensure_ascii=False, indent=2))

    assert not (bad or errors), "\n\n".join(msg_parts)


def testy():
    assert 1 == 1