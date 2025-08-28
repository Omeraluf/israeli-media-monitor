import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

#change the date of the articles.csv to the latest one
df = pd.read_csv("data/clustered/2025-08-28_16-21-40/articles.csv")

by = df.groupby("cluster")
summary = pd.DataFrame({
    "cluster_size": by.size(),
    "n_sources": by["source"].nunique()
})

# % of clusters with ≥2 sources
pct_clusters_multi = (summary["n_sources"] >= 2).mean() * 100

# % of articles that live in ≥2-source clusters (weighted)
articles_in_multi = df[df["cluster"].isin(summary.index[summary["n_sources"]>=2])]
pct_articles_multi = (len(articles_in_multi) / len(df)) * 100

print(f"Clusters with ≥2 sources: {pct_clusters_multi:.1f}%")
print(f"Articles in ≥2-source clusters: {pct_articles_multi:.1f}%")
print(summary.sort_values(["n_sources","cluster_size"], ascending=False).head(10))

#####################
# Top terms in clusters
def top_terms_for_cluster(df, cid, k=12):
    texts = (df.loc[df.cluster==cid, "title"].fillna("") + " " +
             df.loc[df.cluster==cid, "summary"].fillna("")).tolist()
    v = TfidfVectorizer(
        token_pattern=r"(?u)\b[\u05D0-\u05EA]{2,}\b",  # Hebrew words only
        ngram_range=(1,2), min_df=1, max_df=0.95
    )
    X = v.fit_transform(texts)
    weights = X.mean(axis=0).A1
    feats = v.get_feature_names_out()
    top = sorted(zip(feats, weights), key=lambda x: x[1], reverse=True)[:k]
    return [t for t,_ in top]

# Inspect the 5 biggest clusters
for cid in df["cluster"].value_counts().head(5).index:
    print(f"\n=== Cluster {cid} (size={ (df.cluster==cid).sum() }) ===")
    print(", ".join(top_terms_for_cluster(df, cid)))
    print(df.loc[df.cluster==cid, "title"].head(3).to_list())
