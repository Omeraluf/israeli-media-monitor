import pandas as pd
from pathlib import Path

p = max(Path("data/processed").glob("combined_*.json"))
df = pd.read_json(p)

print("\n== Basic shape ==")
print(df.shape, "rows")

print("\n== Duplicates by URL (should be 0) ==")
dups = df[df["url"].duplicated(keep=False)].sort_values("url")
print(len(dups))
print(dups.head(10)[["source","title","url"]])

print("\n== Top summaries by source ==")
top = (df.assign(summary=df["summary"].fillna(""))
         .groupby(["source","summary"]).size()
         .reset_index(name="n")
         .sort_values("n", ascending=False))
print(top.head(20).to_string(index=False))

print("\n== Any section/hub titles that slipped ==")
sus = df[df["title"].str.len().le(6) | df["title"].isin(["אוכל","תרבות","חדשות","דעה","ספורט","בעולם"])]
print(sus[["source","title","url"]].head(20).to_string(index=False))
