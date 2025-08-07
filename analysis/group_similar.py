import pandas as pd
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from pathlib import Path

# === Load all combined_*.json files ===
processed_dir = Path("data/processed")
all_files = sorted(processed_dir.glob("combined_*.json"))

dfs = []
for file in all_files:
    with open(file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
        dfs.append(pd.DataFrame(articles))
before = len(dfs)
df = pd.concat(dfs, ignore_index=True).drop_duplicates()
after = len(df)
print(f"Loaded {len(df)} total articles from {len(all_files)} files")
print(f"Removed {before - after} duplicates during concatenation")

# === 2. Combine title + summary for clustering ===
df['text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('')

# === 3. TF-IDF vectorization ===
# Load hebrew stopwords from file, thanks to: https://github.com/NNLP-IL/Stop-Words-Hebrew/blob/main/stopswords_list_extend.txt
def load_stopwords(filepath):
    with open(filepath, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

hebrew_stopwords = load_stopwords("utils/hebrew_stopwords.txt")

## @@ keep from here:
vectorizer = TfidfVectorizer(max_df=0.8, min_df=2, stop_words=hebrew_stopwords, ngram_range=(1, 2), analyzer='char_wb')
X = vectorizer.fit_transform(df['text'])

# === 4. Agglomerative Clustering ===
clustering_model = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=1.0,
    affinity='cosine',
    linkage='average'
)
df['cluster_id'] = clustering_model.fit_predict(X.toarray())

# === 5. Save the full set with cluster_id ===
output_file = f"data/final/combined_grouped_{pd.Timestamp.now().date()}.json"
df.drop(columns=['text']).to_json(output_path, orient='records', ensure_ascii=False, indent=2)

print(f"Saved {len(df)} grouped articles to {output_path}")
