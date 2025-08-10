import pandas as pd
from pathlib import Path
from preprocessing import dataframe_hygiene

def test_idempotent_hygiene():
    # build a small df that includes a dupe & boilerplate
    rows = [
        {"title":"תרבות","summary":"", "url":"https://ex.com/section/culture", "source":"x"},
        {"title":"כותרת","summary":"בואו לקרוא עוד", "url":"https://ex.com/a", "source":"x"},
        {"title":"כותרת","summary":"בואו לקרוא עוד", "url":"https://ex.com/a?utm=1", "source":"x"},
    ]
    r1 = dataframe_hygiene(rows)
    r2 = dataframe_hygiene(r1)  # running twice shouldn’t change anything
    assert r1 == r2

def test_no_nat_strings(tmp_path):
    rows = [{"title":"כותרת","summary":"","url":"https://ex.com/a","source":"x","published_iso":""}]
    out = dataframe_hygiene(rows)
    for r in out:
        assert r.get("published_iso","") != "NaT"
