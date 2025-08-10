import re
from datetime import datetime
# from preprocessing import (
#     clean_title, normalize_summary,
#     #   canonicalize_url, extract_url_id,
#     # looks_like_section_row, fix_summary_published, parse_any_dt
# )
from analysis.preprocessing import clean_title, normalize_summary

def test_clean_title_basic():
    assert clean_title(" שלום, עולם! ") == "שלום עולם"

def test_normalize_summary_trims_and_spaces():
    assert normalize_summary("  היי   לך  ") == "היי לך"

# def test_canonicalize_url_and_id():
#     u = "https://C14.co.il/article/ARTICLE/1288009/?utm=abc#frag"
#     assert canonicalize_url(u) == "https://c14.co.il/article/1288009"
#     assert extract_url_id(u) == "1288009"

# def test_looks_like_section_row():
#     assert looks_like_section_row("תרבות", "https://ex.com/section/culture") is True
#     assert looks_like_section_row("כותרת רגילה", "https://ex.com/article/123") is False

# def test_fix_summary_published_swap():
#     r = {"summary":"לפני שעה", "published":"זה משפט בעברית עם תוכן."}
#     out = fix_summary_published(r)
#     assert out["summary"].startswith("זה משפט")
#     assert out["published"] == ""

# def test_parse_any_dt():
#     assert isinstance(parse_any_dt("2025-08-10T11:22:33"), datetime)
#     assert isinstance(parse_any_dt("Sun, 10 Aug 2025 11:22:33 +0300"), datetime)
#     assert parse_any_dt("") is None
