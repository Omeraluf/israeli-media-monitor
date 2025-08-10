import json, shutil
from pathlib import Path
import pandas as pd
import importlib

import json, shutil, sys, importlib, os
from pathlib import Path

import json, shutil, sys, importlib, os
from pathlib import Path

import json, shutil, sys, importlib
from pathlib import Path

def run_with_fixture(tmp_path: Path, fixture_name: str):
    raw_dir = tmp_path / "data/raw"
    proc_dir = tmp_path / "data/processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 1) Copy the requested fixture
    src = Path("tests/fixtures/raw") / f"{fixture_name}.json"
    dst = raw_dir / "fixture.json"
    shutil.copy(src, dst)

    # (Optional but useful) sanity check we copied what we think we did
    # Load the just-copied fixture and assert it contains the marker URLs/titles
    copied = json.loads(dst.read_text(encoding="utf-8"))
    assert isinstance(copied, list) and len(copied) > 0, "Empty fixture?"
    # lightweight guard so url_dup can't masquerade as crosstalk, and vice-versa
    if fixture_name == "crosstalk":
        assert all("u" in rec.get("url","") for rec in copied), "Wrong fixture copied for crosstalk"
    if fixture_name == "url_dup":
        assert any("/a" in rec.get("url","") for rec in copied), "Wrong fixture copied for url_dup"

    # 2) Ensure project root is importable
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # 3) Hard reset module cache (parent + submodule) so globals aren’t reused
    sys.modules.pop("analysis.preprocessing", None)
    sys.modules.pop("analysis", None)

    # 4) Fresh import, then override module-level dirs
    prep = importlib.import_module("analysis.preprocessing")
    prep.RAW_DIR = raw_dir
    prep.PROCESSED_DIR = proc_dir
    prep.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 5) Run and read THIS test’s output
    prep.main()
    out_path = max(proc_dir.glob("combined_*.json"))
    return json.loads(out_path.read_text(encoding="utf-8"))


def normalize_rows(rows):
    # Drop volatile fields; sort for stable compare
    keep = []
    for r in rows:
        r = dict(r)
        r.pop("scraped_at", None)
        # keep published_iso but ensure string
        r["published_iso"] = r.get("published_iso","")
        keep.append(r)
    # sort by source+url to stabilize
    keep.sort(key=lambda x: (x.get("source",""), x.get("url","")))
    return keep

def test_url_dedup(tmp_path):
    out = normalize_rows(run_with_fixture(tmp_path, "url_dup"))
    expected = normalize_rows(json.loads(Path("tests/fixtures/expected/url_dup.json").read_text(encoding="utf-8")))
    assert out == expected

def test_crosstalk_fix(tmp_path):
    out = normalize_rows(run_with_fixture(tmp_path, "crosstalk"))
    expected = normalize_rows(json.loads(Path("tests/fixtures/expected/crosstalk.json").read_text(encoding="utf-8")))
    assert out == expected
