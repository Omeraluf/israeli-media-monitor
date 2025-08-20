import importlib
import re
from datetime import datetime, date
import pytest

# Import the module under test. Run pytest from the repo root.
mod = importlib.import_module("analysis.preprocessing")

def has_fn(name: str) -> bool:
    return hasattr(mod, name) and callable(getattr(mod, name))

# -------------------- clean_title --------------------
@pytest.mark.skipif(not has_fn("clean_title"), reason="clean_title() not implemented")
@pytest.mark.parametrize(
    "raw,expected",
    [
        # punctuation stripping + collapse + lowercase
        ("  שלום, עולם!!  ", "שלום עולם"),
        # emoji / ascii artifacts removed
        ("חדשות היום 📰🔥  ", "חדשות היום"),
        # control-ish artifacts removed/collapsed
        ("כותרת\x00  עם  NUL", "כותרת עם nul"),
        # extra spaces / tabs / newlines
        ("זה   טקסט \tעם   רווחים\nמרובים ", "זה טקסט עם רווחים מרובים"),
        # quotes/dashes stripped, Hebrew preserved, lowercase
        ('"הצהרה" – בדיקה', "הצהרה בדיקה"),
        # English/Hebrew mix, punctuation gone, lowercase
        ("Breaking: חדשות-חמות!!", "breaking חדשותחמות"),
    ],
)
def test_clean_title_basic(raw, expected):
    clean_title = getattr(mod, "clean_title")
    out = clean_title(raw)
    out_norm = re.sub(r"\s+", " ", out).strip()
    exp_norm = re.sub(r"\s+", " ", expected).strip()
    assert out_norm == exp_norm

@pytest.mark.skipif(not has_fn("clean_title"), reason="clean_title() not implemented")
def test_clean_title_hebrew_preserved():
    clean_title = getattr(mod, "clean_title")
    raw = "תרבות: מוזיקה קלאסית – קונצרט חורף"
    out = clean_title(raw)
    assert "תרבות" in out and "מוזיקה" in out and "קלאסית" in out
    assert ":" not in out and "–" not in out
    assert out == out.lower()

# -------------------- normalize_summary --------------------
@pytest.mark.skipif(not has_fn("normalize_summary"), reason="normalize_summary() not implemented")
@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, ""),
        ("", ""),
        ("  זה סיכום   קצר  ", "זה סיכום קצר"),
        ("\nשורה ראשונה\nשורה שניה\t", "שורה ראשונה שורה שניה"),
        (123, ""),  # non-str becomes ""
    ],
)
def test_normalize_summary_basic(raw, expected):
    normalize_summary = getattr(mod, "normalize_summary")
    out = normalize_summary(raw)
    out_norm = re.sub(r"\s+", " ", out).strip()
    exp_norm = re.sub(r"\s+", " ", expected).strip()
    assert out_norm == exp_norm

# -------------------- preprocess (pure list->list) --------------------
@pytest.mark.skipif(not has_fn("preprocess"), reason="preprocess() not implemented")
def test_preprocess_filters_category_titles():
    preprocess = getattr(mod, "preprocess")
    records = [
        {"title": "תרבות", "summary": "x", "published_iso": "2025-08-19T10:00:00+00:00"},
        {"title": "כותרת אמיתית", "summary": "  סיכום  ", "published_iso": "2025-08-19T10:00:00+00:00"},
    ]
    out = preprocess(records)
    assert len(out) == 1
    assert out[0]["title"] == "כותרת אמיתית"
    assert out[0]["summary"] == "סיכום"
    assert "clean_title" in out[0] and out[0]["clean_title"] == "כותרת אמיתית".lower()

@pytest.mark.skipif(not has_fn("preprocess"), reason="preprocess() not implemented")
def test_preprocess_published_iso_and_dedup_key():
    preprocess = getattr(mod, "preprocess")
    records = [
        {"title": "A", "summary": None, "published_iso": "2025-08-19T12:34:56+00:00"},
        {"title": "B", "summary": "  ", "published_iso": "bad-date"},
        {"title": "C", "summary": "x"},  # missing published_iso
    ]
    out = preprocess(records)
    # Record 0: valid dt
    assert isinstance(out[0]["published_dt"], datetime)
    assert out[0]["dedup_key"].startswith(out[0]["clean_title"] + "_")
    assert str(out[0]["published_dt"].date()) in out[0]["dedup_key"]
    # Record 1: invalid dt -> None + published_iso blanked
    assert out[1]["published_dt"] is None and out[1]["published_iso"] == ""
    assert out[1]["dedup_key"].endswith("_no-date")
    # Record 2: missing dt -> None + no-date
    assert out[2]["published_dt"] is None and out[2]["published_iso"] == ""
    assert out[2]["dedup_key"].endswith("_no-date")

# -------------------- dataframe_hygiene --------------------
@pytest.mark.skipif(not has_fn("dataframe_hygiene"), reason="dataframe_hygiene() not implemented")
def test_dataframe_hygiene_drops_category_and_dedups_urls():
    dataframe_hygiene = getattr(mod, "dataframe_hygiene")
    today = datetime(2025, 8, 19, 9, 0, 0)
    records = [
        # Category-only title -> should drop
        {"title": "חדשות", "summary": "x", "source": "kan11", "url": "u1", "published_dt": today},
        # Keep this, later duplicate URL should be dropped
        {"title": "כותרת A", "summary": "s", "source": "kan11", "url": "dup", "published_dt": today},
        {"title": "כותרת B", "summary": "s", "source": "kan11", "url": "dup", "published_dt": today},
        # Keep: empty URL should not interfere with dedup
        {"title": "כותרת C", "summary": "s", "source": "kan11", "url": "", "published_dt": today},
        {"title": "כותרת D", "summary": "s", "source": "kan11", "url": None, "published_dt": today},
    ]
    out = dataframe_hygiene(records)
    urls = [r["url"] for r in out]
    titles = [r["title"] for r in out]
    # Category row gone
    assert "חדשות" not in titles
    # Only first 'dup' kept
    assert urls.count("dup") == 1
    # Empty/None URL rows preserved
    assert "" in urls and None in urls
    # dedup_key rebuilt correctly (clean_title + date)
    for r in out:
        dkey = r["dedup_key"]
        assert dkey.startswith(r["clean_title"] + "_")
        if isinstance(r.get("published_dt"), datetime):
            assert str(r["published_dt"].date()) in dkey
        else:
            assert dkey.endswith("_no-date")

@pytest.mark.skipif(not has_fn("dataframe_hygiene"), reason="dataframe_hygiene() not implemented")
def test_dataframe_hygiene_removes_boilerplate_per_source():
    dataframe_hygiene = getattr(mod, "dataframe_hygiene")
    # Construct 10 rows for source 's1' where one summary repeats 5 times (>=5 and ratio >= 0.5)
    dt = datetime(2025, 8, 19, 8, 0, 0)
    boiler = "ברוכים הבאים לאתר"
    records = []
    # 5 boilerplate rows (should be removed)
    for i in range(5):
        records.append({"title": f"כתבה {i}", "summary": boiler, "source": "s1", "url": f"b{i}", "published_dt": dt})
    # 5 unique rows (should remain)
    for i in range(5, 10):
        records.append({"title": f"כתבה {i}", "summary": f"סיכום {i}", "source": "s1", "url": f"u{i}", "published_dt": dt})
    # Also add some rows for s2 (different source) to ensure independence
    for i in range(3):
        records.append({"title": f"ס2-{i}", "summary": boiler, "source": "s2", "url": f"s2-{i}", "published_dt": dt})

    out = dataframe_hygiene(records)
    summaries = [r["summary"] for r in out if r["source"] == "s1"]
    # s1: boilerplate removed; only the 5 non-boiler rows remain
    assert all(s.startswith("סיכום ") for s in summaries)
    # s2: ratio is 3/3 (>= 0.5 and count >=5? No, count=3 < 5) -> should NOT be removed
    assert any(r for r in out if r["source"] == "s2" and r["summary"] == boiler)

# -------------------- Optional helpers (not present yet) --------------------
@pytest.mark.skipif(not has_fn("canonicalize_url"), reason="canonicalize_url() not implemented")
def test_canonicalize_url_placeholder():
    assert True  # replace once helper is added

@pytest.mark.skipif(not has_fn("extract_url_id"), reason="extract_url_id() not implemented")
def test_extract_url_id_placeholder():
    assert True  # replace once helper is added

@pytest.mark.skipif(not has_fn("looks_like_section_row"), reason="looks_like_section_row() not implemented")
def test_looks_like_section_row_placeholder():
    assert True  # replace once helper is added

@pytest.mark.skipif(not has_fn("parse_any_dt"), reason="parse_any_dt() not implemented")
def test_parse_any_dt_placeholder():
    assert True  # replace once helper is added
