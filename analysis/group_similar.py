# analysis/group_similar.py
import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from scipy.sparse import hstack

OUTPUT_PATH = Path("data/final")
PROCESSED_DIR = Path("data/processed")
STOPWORDS_PATH = Path("analysis/utils/hebrew_stopswords_list_extended.txt")

def load_stopwords(filepath: Path):
    try:
        with open(filepath, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[warn] stopwords file not found at {filepath}; continuing without stopwords.")
        return None

def load_processed_frames(processed_dir: Path) -> pd.DataFrame:
    files = sorted(processed_dir.glob("combined_*.json"))
    print(f"Loading {len(files)} files from {processed_dir}...")
    if not files:
        raise SystemExit(f"No processed files found in {processed_dir}. Run preprocessing first.")
    dfs = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            articles = json.load(f)
        df_i = pd.DataFrame(articles)
        df_i["_from_file"] = file.name
        dfs.append(df_i)
    df_combined = pd.concat(dfs, ignore_index=True)
    before = len(df_combined)
    df = df_combined.drop_duplicates(subset=["title", "summary"]).copy()
    after = len(df)
    print(
        f"Loaded {after} unique articles (removed {before - after} dups, "
        f"{(before - after) / max(before,1):.1%})"
    )
    return df

def vectorize(df: pd.DataFrame, stopwords):
    print("Combining title and summary for clustering...")
    df.loc[:, "text"] = df.get("title_sanitized","").fillna("") + " " + df.get("summary_sanitized","").fillna("")

    print("Vectorizing text with TF-IDF...")
    # char n-grams help for Hebrew; words with stopwords for semantics
    char_vectorizer = TfidfVectorizer(max_df=0.8, min_df=2, ngram_range=(3, 5), analyzer="char_wb") 
    word_vectorizer = TfidfVectorizer(
        max_df=0.85, min_df=2, ngram_range=(1, 2),
        analyzer="word", stop_words=stopwords
    )   
    

    X_char = char_vectorizer.fit_transform(df["text"])
    X_word = word_vectorizer.fit_transform(df["text"])
    X = hstack([X_word, X_char])
    return df, X

def cluster(df: pd.DataFrame, X, distance_threshold: float):
    print("Clustering articles using Agglomerative Clustering...")
    # NOTE: AgglomerativeClustering with cosine currently requires a dense array;
    # X.toarray() may be memory-heavy for very large corpora.
    try:
        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage="average",
            metric="cosine",  # sklearn >=1.2
        )
    except TypeError:
        # Older sklearn versions use 'affinity' instead of 'metric'
        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage="average",
            affinity="cosine",
        )
    labels = model.fit_predict(X.toarray())  # ⚠️ may be heavy if many rows
    df = df.copy()
    df["cluster_id"] = labels
    return df

def save(df: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / f"combined_grouped_{pd.Timestamp.now().date()}.json"
    df.drop(columns=["text"], errors="ignore").to_json(out_json, orient="records", force_ascii=False, indent=2)
    print(f"Saved {len(df)} grouped articles to {out_json}")
    return out_json

def main(argv=None):
    ap = argparse.ArgumentParser(description="Group similar news articles.")
    ap.add_argument("--processed-dir", default=str(PROCESSED_DIR), help="Directory with combined_*.json files")
    ap.add_argument("--out", default=str(OUTPUT_PATH), help="Output directory")
    ap.add_argument("--distance-threshold", type=float, default=0.85, help="Agglomerative distance threshold")
    args = ap.parse_args(argv)

    df = load_processed_frames(Path(args.processed_dir))
    stopwords = load_stopwords(STOPWORDS_PATH)
    df, X = vectorize(df, stopwords)
    df = cluster(df, X, args.distance_threshold)
    save(df, Path(args.out))

if __name__ == "__main__":
    main()
