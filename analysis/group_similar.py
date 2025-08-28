# # analysis/group_similar.py
# import argparse
# import json
# from pathlib import Path

# import pandas as pd
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.cluster import AgglomerativeClustering
# from scipy.sparse import hstack

# OUTPUT_PATH = Path("data/final")
# PROCESSED_DIR = Path("data/processed")
# STOPWORDS_PATH = Path("analysis/utils/hebrew_stopswords_list_extended.txt")

# def load_stopwords(filepath: Path):
#     try:
#         with open(filepath, encoding="utf-8") as f:
#             return [line.strip() for line in f if line.strip()]
#     except FileNotFoundError:
#         print(f"[warn] stopwords file not found at {filepath}; continuing without stopwords.")
#         return None

# def load_processed_frames(processed_dir: Path) -> pd.DataFrame:
#     files = sorted(processed_dir.glob("combined_*.json"))
#     print(f"Loading {len(files)} files from {processed_dir}...")
#     if not files:
#         raise SystemExit(f"No processed files found in {processed_dir}. Run preprocessing first.")
#     dfs = []
#     for file in files:
#         with open(file, "r", encoding="utf-8") as f:
#             articles = json.load(f)
#         df_i = pd.DataFrame(articles)
#         df_i["_from_file"] = file.name
#         dfs.append(df_i)
#     df_combined = pd.concat(dfs, ignore_index=True)
#     before = len(df_combined)
#     df = df_combined.drop_duplicates(subset=["title", "summary"]).copy()
#     after = len(df)
#     print(
#         f"Loaded {after} unique articles (removed {before - after} dups, "
#         f"{(before - after) / max(before,1):.1%})"
#     )
#     return df

# def vectorize(df: pd.DataFrame, stopwords):
#     print("Combining title and summary for clustering...")
#     df.loc[:, "text"] = df.get("title_sanitized","").fillna("") + " " + df.get("summary_sanitized","").fillna("")

#     print("Vectorizing text with TF-IDF...")
#     # char n-grams help for Hebrew; words with stopwords for semantics
#     char_vectorizer = TfidfVectorizer(max_df=0.8, min_df=2, ngram_range=(3, 5), analyzer="char_wb") 
#     word_vectorizer = TfidfVectorizer(
#         max_df=0.85, min_df=2, ngram_range=(1, 2),
#         analyzer="word", stop_words=stopwords
#     )   
    

#     X_char = char_vectorizer.fit_transform(df["text"])
#     X_word = word_vectorizer.fit_transform(df["text"])
#     X = hstack([X_word, X_char])
#     return df, X

# def cluster(df: pd.DataFrame, X, distance_threshold: float):
#     print("Clustering articles using Agglomerative Clustering...")
#     # NOTE: AgglomerativeClustering with cosine currently requires a dense array;
#     # X.toarray() may be memory-heavy for very large corpora.
#     try:
#         model = AgglomerativeClustering(
#             n_clusters=None,
#             distance_threshold=distance_threshold,
#             linkage="average",
#             metric="cosine",  # sklearn >=1.2
#         )
#     except TypeError:
#         # Older sklearn versions use 'affinity' instead of 'metric'
#         model = AgglomerativeClustering(
#             n_clusters=None,
#             distance_threshold=distance_threshold,
#             linkage="average",
#             affinity="cosine",
#         )
#     labels = model.fit_predict(X.toarray())  # ⚠️ may be heavy if many rows
#     df = df.copy()
#     df["cluster_id"] = labels
#     return df

# def save(df: pd.DataFrame, output_dir: Path):
#     output_dir.mkdir(parents=True, exist_ok=True)
#     out_json = output_dir / f"combined_grouped_{pd.Timestamp.now().date()}.json"
#     df.drop(columns=["text"], errors="ignore").to_json(out_json, orient="records", force_ascii=False, indent=2)
#     print(f"Saved {len(df)} grouped articles to {out_json}")
#     return out_json

# def main(argv=None):
#     ap = argparse.ArgumentParser(description="Group similar news articles.")
#     ap.add_argument("--processed-dir", default=str(PROCESSED_DIR), help="Directory with combined_*.json files")
#     ap.add_argument("--out", default=str(OUTPUT_PATH), help="Output directory")
#     ap.add_argument("--distance-threshold", type=float, default=0.85, help="Agglomerative distance threshold")
#     args = ap.parse_args(argv)

#     df = load_processed_frames(Path(args.processed_dir))
#     stopwords = load_stopwords(STOPWORDS_PATH)
#     df, X = vectorize(df, stopwords)
#     df = cluster(df, X, args.distance_threshold)
#     save(df, Path(args.out))

# if __name__ == "__main__":
#     main()



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal, single-file clustering for 'Israeli Media Monitor'.

What it does (simple & robust):
1) Loads articles from JSON/JSONL under data/processed/.
2) Builds a text field: title + " " + summary (use your normalized versions if you have them).
3) TF-IDF vectorizes (uni+bi-grams by default).
4) Computes cosine distance and runs Agglomerative Clustering with a distance threshold.
5) Prints cluster stats and a few sample clusters.

Usage:
  python cluster_simple.py
  python cluster_simple.py --threshold 0.84 --min-df 2 --max-df 0.85 --ngrams 1 2 --max-articles 3000

Notes:
- Keep threshold around 0.80–0.90. Lower = bigger clusters, Higher = more, smaller clusters.
- This builds a full distance matrix (O(n^2) memory). Start with <= ~2000 articles.
"""

import json
import argparse
from glob import glob
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances
import os, json, time
from pathlib import Path
from scipy.sparse import hstack

STOPWORDS_PATH = Path("analysis/utils/hebrew_stopswords_list_extended.txt")

def load_articles(processed_dir: str) -> pd.DataFrame:
    """
    Loads records from .json (list of dicts) and .jsonl (one JSON per line).
    Expects keys: 'title', 'summary', 'source', 'url', 'published' (best-effort).
    """
    records = []
    p = Path(processed_dir)
    files = list(p.glob("*.json")) + list(p.glob("*.jsonl"))
    for f in files:
        try:
            if f.suffix == ".jsonl":
                with f.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        records.append(obj)
            else:
                with f.open("r", encoding="utf-8") as fh:
                    obj = json.load(fh)
                    if isinstance(obj, list):
                        records.extend(obj)
                    elif isinstance(obj, dict) and "records" in obj:
                        records.extend(obj["records"])
        except Exception as e:
            print(f"[WARN] Failed reading {f}: {e}")

    if not records:
        print("[WARN] No records found in", processed_dir)

    # Normalize to dataframe with safe defaults
    df = pd.DataFrame.from_records(records)
    for col in ["title", "summary", "source", "url", "published"]:
        if col not in df.columns:
            df[col] = ""

    # Prefer normalized fields if you keep both versions
    # e.g., df["title_use"] = df.get("title_norm_min", df["title"])
    df["title_use"] = df["title_norm_min"].fillna("").astype(str)
    df["summary_use"] = df["summary_norm_min"].fillna("").astype(str)

    # Build the clustering text     # more weight to the title in the TFIDF
    df["text_for_cluster"] = (df["title_use"]).str.strip()                    #@@@@@@@@@ Maybe add the summary later       # + " " + df["title_use"]        #+ " " + df["summary_use"]
    # Drop empty
    df = df[df["text_for_cluster"].str.len() > 0].reset_index(drop=True)
    return df


def load_stopwords(path: str):
    p = Path(path)
    words = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            w = line.strip()
            if not w or w.startswith("#"):
                continue
            words.append(w)
    return sorted(set(words))


def cluster(df: pd.DataFrame,
            threshold: float = 0.85,
            ngram_low: int = 1,
            ngram_high: int = 2,
            min_df: int = 2,
            max_df: float = 0.8,
            max_articles: int = 2000):
    """
    Returns labels (np.array) aligned to df rows.
    """

    if len(df) == 0:
        return np.array([])

    if len(df) > max_articles:
        print(f"[INFO] Truncating from {len(df)} to max_articles={max_articles} to keep it simple.")
        df = df.iloc[:max_articles].copy()

    texts = df["text_for_cluster"].tolist()

    he_stop = load_stopwords(STOPWORDS_PATH) if STOPWORDS_PATH.exists() else None

    vectorizer_word = TfidfVectorizer(
        ngram_range=(ngram_low, ngram_high),
        min_df=min_df,
        max_df=max_df,
        stop_words=he_stop
    )

    
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ maybe open the CHAR vectorizer later
    # vectorizer_char = TfidfVectorizer(
    # analyzer="char",
    # ngram_range=(3,5),
    # min_df=2,
    # max_df=0.8,
    # )
    # X_word = vectorizer_word.fit_transform(texts)
    # X_char = vectorizer_char.fit_transform(texts)

    # # Optionally down-weight char features a bit
    # X = hstack([X_word, X_char * 0.5])
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    X = vectorizer_word.fit_transform(texts)

    # AgglomerativeClustering with precomputed cosine distances
    print("[INFO] Computing cosine distance matrix (may take time for large N)…")
    D = pairwise_distances(X, metric="cosine")

    model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=threshold,
        metric="precomputed",   # sklearn >= 1.2
        linkage="average"
    )
    labels = model.fit_predict(D)

    return df, labels


def show_report(df: pd.DataFrame, labels: np.ndarray, top_k: int = 10, sample_per_cluster: int = 3):
    if labels.size == 0:
        print("[INFO] Nothing to cluster.")
        return

    df = df.copy()
    df["cluster"] = labels

    counts = Counter(labels)
    n_clusters = len(counts)
    singletons = sum(1 for _, c in counts.items() if c == 1)

    print("@@@@@@@@@@@@@@@@@@@ -- CLUSTER REPORT -- @@@@@@@@@@@@@@@@@@@@@@")
    print(f"Total articles: {len(df)}")
    print(f"Clusters: {n_clusters}")
    print(f"Singleton clusters (size=1): {singletons} ({singletons/max(1,len(df))*100:.1f}%)\n")

    print("Top cluster sizes:")
    for cid, c in counts.most_common(top_k):
        print(f"  cluster {cid}: {c}")
    print()

    # Show samples for the biggest clusters
    biggest = [cid for cid, _ in counts.most_common(top_k)]
    for cid in biggest:
        sub = df[df["cluster"] == cid].head(sample_per_cluster)
        print(f"=== Cluster {cid} (showing {len(sub)} of {counts[cid]}) ===")
        for _, row in sub.iterrows():
            title = str(row.get("title", ""))[:200]
            source = row.get("source", "")
            url = row.get("url", "")
            published = row.get("published", "")
            print(f" - [{source}] {title}")
            if published:
                print(f"   published: {published}")
            if url:
                print(f"   url: {url}")
        print()


def save_cluster_outputs(df, labels, out_dir="data/clustered", save="both", run_params=None):
    """
    Save per-article table (CSV) + per-cluster nested (JSONL).
    Creates a timestamped folder: data/clustered/2025-08-28_15-12-03/
    """
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    out_base = Path(out_dir) / ts
    out_base.mkdir(parents=True, exist_ok=True)

    # Attach labels + cluster sizes
    df_out = df.copy()
    df_out["cluster"] = labels
    sizes = df_out.groupby("cluster").size().rename("cluster_size").reset_index()
    df_out = df_out.merge(sizes, on="cluster", how="left")

    # Nice column order for quick review
    cols = [c for c in ["cluster","cluster_size","source","published","title","summary","url"]
            if c in df_out.columns]
    cols = cols + [c for c in df_out.columns if c not in cols]  # keep everything else after

    # 1) Article-level CSV
    if save in ("csv","both"):
        csv_path = out_base / "articles.csv"
        df_out.to_csv(csv_path, index=False, encoding="utf-8-sig")
        # Cluster summary CSV (sizes + example title)
        summary = (df_out.groupby("cluster")
                   .agg(cluster_size=("cluster","size"),
                        sources=("source", lambda s: ", ".join(sorted({x for x in s if x})[:5])),
                        example_title=("title","first")))
        summary = summary.sort_values("cluster_size", ascending=False).reset_index()
        summary.to_csv(out_base / "clusters_summary.csv", index=False, encoding="utf-8-sig")

    # 2) Cluster-level JSONL (nested items)
    if save in ("json","both"):
        jsonl_path = out_base / "clusters.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as f:
            for cid, sub in df_out.sort_values(["cluster","published"]).groupby("cluster"):
                record = {
                    "cluster": int(cid),
                    "size": int(sub.shape[0]),
                    "items": sub[["source","title","summary","url","published"]]
                                .to_dict(orient="records")
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Tiny README with stats
    readme = out_base / "README.txt"
    with readme.open("w", encoding="utf-8") as f:
        n_articles = len(df_out)
        n_clusters = df_out["cluster"].nunique()
        n_singletons = int((df_out.groupby("cluster").size() == 1).sum())
        f.write(
            f"Articles: {n_articles}\n"
            f"Clusters: {n_clusters}\n"
            f"Singletons: {n_singletons} ({n_singletons/max(1,n_articles)*100:.1f}%)\n"
            f"\nFiles:\n- articles.csv\n- clusters_summary.csv\n- clusters.jsonl\n"
        )
        if run_params:
            f.write("\nRun params:\n")
            # print only keys that have values
            for k in ["threshold","analyzer","ngrams","min_df","max_df","title_weight",
                      "processed_dir","max_articles","window_days","window_hours",
                      "date_from","date_to","stopwords"]:
                v = run_params.get(k, None)
                if v not in (None, "", []):
                    f.write(f"- {k}: {v}\n")

    print(f"[INFO] Saved outputs to {out_base}")



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--processed-dir", default="data/processed", help="Folder with processed .json/.jsonl")
    ap.add_argument("--threshold", type=float, default=0.83, help="Distance threshold (0–1, cosine distance)")
    ap.add_argument("--min-df", type=int, default=2, help="Ignore terms that appear in fewer than min_df docs")
    ap.add_argument("--max-df", type=float, default=0.75, help="Ignore terms that appear in more than max_df fraction")
    ap.add_argument("--ngrams", nargs=2, type=int, default=[1, 2], help="n-gram range, e.g. --ngrams 1 2")
    ap.add_argument("--max-articles", type=int, default=2000, help="Cap to avoid huge distance matrices")
    ap.add_argument("--date-from", type=str, default=None, help="Start date (YYYY-MM-DD), inclusive")
    ap.add_argument("--date-to",   type=str, default=None, help="End date (YYYY-MM-DD), inclusive")
    ap.add_argument("--window-days", type=int, default=2, help="Keep only the last N whole days (by published date)")
    ap.add_argument("--window-hours", type=int, default=None, help="Keep only the last N hours (rolling window)")
    # ap.add_argument("--char", action="store_true", help="Use character 3–5 TF-IDF instead of word 1–2")

    ap.add_argument("--out-dir", default="data/clustered")
    ap.add_argument("--save", choices=["csv","json","both"], default="both")

    args = ap.parse_args()

    df = load_articles(args.processed_dir)
    print(f"[INFO] Loaded {len(df)} articles from {args.processed_dir}")

    ############### Dedup before building text for clustering
    # Parse published -> _dt (UTC), then sort so "keep='last'" is meaningful
    if "published" not in df.columns:
        df["published"] = None

    df["_dt"] = pd.to_datetime(df["published"], utc=True, errors="coerce")
    df = df.sort_values("_dt", na_position="first")

    # Dedup within each source by normalized title (keep latest)
    df = (df
        .drop_duplicates(subset=["source", "title_norm_min"], keep="last")
        .reset_index(drop=True))

    ###############

    df2, labels = cluster(
        df,
        threshold=args.threshold,
        ngram_low=args.ngrams[0],
        ngram_high=args.ngrams[1],
        min_df=args.min_df,
        max_df=args.max_df,
        max_articles=args.max_articles
        # use_char=args.char
    )

    #show_report(df2, labels)

    run_params = {
    "threshold": args.threshold,
    "analyzer": "char" if getattr(args, "char", False) else "word",
    "ngrams": tuple(args.ngrams),
    "min_df": args.min_df,
    "max_df": args.max_df,
    "title_weight": getattr(args, "title_weight", 1),
    "processed_dir": args.processed_dir,
    "max_articles": args.max_articles,
    "window_days": getattr(args, "window_days", None),
    "window_hours": getattr(args, "window_hours", None),
    "date_from": getattr(args, "date_from", None),
    "date_to": getattr(args, "date_to", None),
    "stopwords": getattr(args, "stopwords", None),
    }
    save_cluster_outputs(df2, labels, out_dir=args.out_dir, save=args.save, run_params=run_params)


if __name__ == "__main__":
    main()
