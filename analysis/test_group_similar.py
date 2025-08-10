import pandas as pd
from pathlib import Path

print("@@@@@@@@@@@@@@@@@@@ -- TESTING -- @@@@@@@@@@@@@@@@@@@@@@")

INPUT_FILE = Path("data/final/combined_grouped_2025-08-10.json")  # change date or use latest

df = pd.read_json(INPUT_FILE, orient='records')

# 1) Cluster size stats
sizes = df['cluster_id'].value_counts().sort_values(ascending=False)
print("Clusters:", sizes.shape[0])
print("Total articles:", len(df))
print("Singleton clusters (size=1):", (sizes==1).sum(), f"({(sizes==1).mean():.1%})")
print("\nTop 10 cluster sizes:\n", sizes.head(10))

# 2) Preview a few clusters
def preview_cluster(cid, k=3):
    cols = [c for c in ['published','source','title','summary','url'] if c in df.columns]
    print(f"\n=== Cluster {cid} (n={len(df[df['cluster_id']==cid])}) ===")
    print(df.loc[df['cluster_id']==cid, cols].head(k))

for cid in sizes.head(5).index:
    preview_cluster(cid, k=3)

# 3) Export preview CSV
preview_cols = [c for c in ['cluster_id','published','source','title','summary','url'] if c in df.columns]
output_path = Path("data/final/combined_grouped_preview.csv")
df.sort_values(['cluster_id','published']).to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"Preview CSV saved to {output_path}")


print("@@@@@@@@@@@@@@@@@@@ -- TESTING -- @@@@@@@@@@@@@@@@@@@@@@")
