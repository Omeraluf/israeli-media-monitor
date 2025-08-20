# postprocess_clusters.py
import json, os, argparse
from datetime import datetime
import pandas as pd

def parse_dt(s):
    if not isinstance(s, str) or not s.strip():
        return pd.NaT
    return pd.to_datetime(s, utc=True, errors="coerce")

def pick_representative(group: pd.DataFrame) -> pd.Series:
    g = group.copy()
    g["title_len"] = g["title"].apply(lambda x: len(x) if isinstance(x, str) else 0)
    g = g.sort_values(
        by=["published_dt_parsed", "scraped_at_parsed", "title_len"],
        ascending=[True, True, False],
    )
    return g.iloc[0]

def main(inp, out_dir):
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    # Ensure expected columns exist
    for col in ["cluster_id","title","summary","url","source","published_dt","scraped_at","clean_title"]:
        if col not in df.columns:
            df[col] = None

    df["published_dt_parsed"] = df["published_dt"].apply(parse_dt)
    df["scraped_at_parsed"] = df["scraped_at"].apply(parse_dt)

    # Metrics
    n_articles = len(df)
    cluster_counts = df["cluster_id"].value_counts().sort_index()
    n_clusters = cluster_counts.shape[0]
    n_singletons = (cluster_counts == 1).sum()
    pct_singletons = (n_singletons / max(n_clusters, 1)) * 100.0
    print("=== Metrics ===")
    print(f"Articles: {n_articles}")
    print(f"Clusters: {n_clusters}")
    print(f"Singleton clusters: {n_singletons} ({pct_singletons:.1f}%)")
    print("Top 10 cluster sizes:")
    print(cluster_counts.sort_values(ascending=False).head(10))

    # Representatives & exports
    repr_rows, article_rows = [], []
    for cid, group in df.groupby("cluster_id", dropna=False):
        rep = pick_representative(group)
        sources = ", ".join(sorted(set(group["source"].dropna().astype(str).tolist())))
        first_pub = group["published_dt_parsed"].min()
        last_pub = group["published_dt_parsed"].max()
        repr_rows.append({
            "cluster_id": cid,
            "size": len(group),
            "repr_title": rep.get("title",""),
            "repr_url": rep.get("url",""),
            "repr_source": rep.get("source",""),
            "sources": sources,
            "first_published_dt": first_pub.isoformat() if pd.notna(first_pub) else "",
            "last_published_dt": last_pub.isoformat() if pd.notna(last_pub) else "",
        })
        for _, r in group.sort_values(["published_dt_parsed","source","url"]).iterrows():
            article_rows.append({
                "cluster_id": cid,
                "title": r.get("title",""),
                "summary": r.get("summary",""),
                "url": r.get("url",""),
                "source": r.get("source",""),
                "published_dt": r.get("published_dt",""),
                "scraped_at": r.get("scraped_at",""),
            })

    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(repr_rows).sort_values(["size","cluster_id"], ascending=[False,True])\
        .to_csv(os.path.join(out_dir, "clusters_summary.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(article_rows).to_csv(os.path.join(out_dir, "articles_by_cluster.csv"), index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to combined_grouped_YYYY-MM-DD.json")
    ap.add_argument("--out", dest="out_dir", required=True, help="Output directory")
    args = ap.parse_args()
    main(args.inp, args.out_dir)


## Run this script with:
# python analysis/tools/postprocess_clusters.py --in data/final/combined_grouped_YYYY-MM-DD.json --out data/final/