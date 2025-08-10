import pandas as pd
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering
from pathlib import Path
from scipy.sparse import hstack

OUTPUT_PATH = Path("data/final")

# === Load all combined_*.json files ===
processed_dir = Path("data/processed")
all_files = sorted(processed_dir.glob("combined_*.json"))

# === 1. Load and deduplicate articles ===
print(f"Loading {len(all_files)} files from {processed_dir}...")
dfs = []
for file in all_files:
    with open(file, 'r', encoding='utf-8') as f:
        articles = json.load(f)
        df_i = pd.DataFrame(articles)
        df_i['_from_file'] = file.name  # optional: provenance
        dfs.append(df_i)

# Row counts BEFORE/AFTER (use rows, not number of dfs)
df_combined = pd.concat(dfs, ignore_index=True)

before = len(df_combined)
# Pick your dedup key; for news this is usually better than full-row:
# CHANGE: add .copy() to avoid SettingWithCopyWarning later
df = df_combined.drop_duplicates(subset=['title', 'summary']).copy()
after = len(df)

print(f"Loaded {after} total unique articles from {len(all_files)} files")
print(f"Removed {before - after} duplicates during concatenation "
      f"({(before - after) / max(before,1):.1%} of rows)")

# === 2. Combine title + summary for clustering ===
print("Combining title and summary for clustering...")
# CHANGE: use .loc[...] assignment to avoid chained-assignment warning
df.loc[:, 'text'] = df['title'].fillna('') + ' ' + df['summary'].fillna('')


# === 3. TF-IDF vectorization ===
print("Vectorizing text with TF-IDF...")
# Load hebrew stopwords from file, thanks to: https://github.com/NNLP-IL/Stop-Words-Hebrew/blob/main/stopswords_list_extend.txt
def load_stopwords(filepath):
    with open(filepath, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

hebrew_stopwords = load_stopwords("analysis/utils/hebrew_stopswords_list_extended.txt")

##          @@ stop_words=hebrew_stopwords, apply only when analyzer is 'word'
char_vectorizer = TfidfVectorizer(max_df=0.8, min_df=2, ngram_range=(3,5), analyzer='char_wb')
word_vectorizer = TfidfVectorizer(max_df=0.85, min_df=2, ngram_range=(1,2), stop_words=hebrew_stopwords, analyzer='word')

X_char = char_vectorizer.fit_transform(df['text'])
X_word = word_vectorizer.fit_transform(df['text'])
X = hstack([X_word, X_char])

#@@ X = vectorizer.fit_transform(df['text']) ## probably wouldn't need that in the future

# === 4. Agglomerative Clustering ===
print("Clustering articles using Agglomerative Clustering...")
clustering_model = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=0.85,
    metric='cosine',
    linkage='average'
)
df['cluster_id'] = clustering_model.fit_predict(X.toarray())

# === 5. Save the full set with cluster_id ===
print("Saving clustered articles with cluster IDs...")
output_file = OUTPUT_PATH / f"combined_grouped_{pd.Timestamp.now().date()}.json"
df.drop(columns=['text']).to_json(output_file, orient='records', force_ascii=False, indent=2)

print(f"Saved {len(df)} grouped articles to {output_file}")
