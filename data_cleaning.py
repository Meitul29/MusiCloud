import pandas as pd
import ast
import nltk
import joblib
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download tokenizer if not already installed
nltk.download('punkt')
nltk.download('punkt_tab')

stemmer = PorterStemmer()

def tokenization(txt):
    """Tokenizes and stems words, preserving non-alphanumeric integrity where needed."""
    tokens = nltk.word_tokenize(str(txt))
    stemming = [stemmer.stem(w) if w.isalnum() else w for w in tokens]
    return " ".join(stemming)

def clean_hindi_lyrics(lyric_str):
    """Converts the string-list format in clean_data_2.csv into a clean paragraph."""
    try:
        # Safely evaluate the string as a Python list
        lyric_list = ast.literal_eval(lyric_str)
        # Remove the word 'Lyrics' or 'Translation' if it's the first item
        if lyric_list and lyric_list[0] in ['Lyrics', 'Translation']:
            lyric_list = lyric_list[1:]
        # Join the list into a single space-separated string
        return " ".join(lyric_list)
    except:
        return str(lyric_str)

print("Loading datasets...")
# 1. Load both datasets
df_english = pd.read_csv("spotify_millsongdata.csv")
df_hindi = pd.read_csv("clean_data.csv")

print("Formatting datasets...")
# 2. Format the Hindi Dataset
# Apply the lyric cleaning function
df_hindi['text'] = df_hindi['Hindi Lyrics'].apply(clean_hindi_lyrics)
df_hindi['song'] = df_hindi['Song Title']
# Inject a placeholder artist for the API workaround in app.py
df_hindi['artist'] = "Bollywood / Hindi"
df_hindi = df_hindi[['artist', 'song', 'text']]

# 3. Format the English Dataset
if 'link' in df_english.columns:
    df_english = df_english.drop('link', axis=1)
df_english = df_english[['artist', 'song', 'text']]

print("Merging and sampling data...")
# 4. Strategic Sampling (4000 English, 1000 Hindi to maintain balance)
sample_eng = df_english.sample(n=min(4000, len(df_english)), random_state=42).reset_index(drop=True)
sample_hin = df_hindi.sample(n=min(1000, len(df_hindi)), random_state=42).reset_index(drop=True)

# Combine both datasets vertically
df = pd.concat([sample_eng, sample_hin], ignore_index=True)

print("Cleaning text...")
# 5. Normalize text cases and clean line breaks
df['text'] = (
    df['text']
    .str.lower()
    .replace(r'^\w\s', ' ', regex=True)
    .replace(r'\n', ' ', regex=True)
)

print("Applying NLP Tokenization...")
# 6. Apply NLTK Tokenization
df['text'] = df['text'].apply(tokenization)

print("Calculating TF-IDF and Cosine Similarity...")
# 7. TF-IDF Vectorization (stop_words='english' removed to preserve Hindi terms)
tfidf = TfidfVectorizer(analyzer='word')
matrix = tfidf.fit_transform(df['text'])

# 8. Compute Cosine Similarity Matrix
similarity = cosine_similarity(matrix)

print("Exporting model artifacts...")
# 9. Save Compressed Artifacts
joblib.dump(df, 'df.pkl', compress=3)
joblib.dump(similarity, 'similarity.pkl', compress=9)

print("✅ Processing Completed! Mixed Dataset Ready.")
