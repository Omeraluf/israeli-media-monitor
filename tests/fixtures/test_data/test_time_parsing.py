from datetime import timedelta
from adapters.c14_adapter import parse_hebrew_time_label, is_time_label

def test_is_time_label_positive():
    for s in ["לפני שעה", "לפני 3 שעות", "לפני דקה", "לפני 2 ימים"]:
        assert is_time_label(s) is True

def test_is_time_label_negative():
    for s in ["כותרת כתבה", "טקסט רגיל", ""]:
        assert is_time_label(s) is False

def test_parse_hebrew_time_label(base_now):
    cases = [
        ("לפני דקה",  timedelta(minutes=1)),
        ("לפני שעה",  timedelta(hours=1)),
        ("לפני 3 שעות", timedelta(hours=3)),
        ("לפני יום",  timedelta(days=1)),
        ("לפני 2 ימים", timedelta(days=2)),
    ]
    for text, delta in cases:
        got = parse_hebrew_time_label(text, now=base_now)
        assert got == (base_now - delta).isoformat(timespec="seconds")
