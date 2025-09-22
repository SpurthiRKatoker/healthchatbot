import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string
import re

# --- Load preprocessed vocab ---
with open("data/symptom_vocab.txt", "r", encoding="utf-8") as f:
    symptoms = [line.strip() for line in f if line.strip()]

# --- Preprocess function ---
def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)   # remove punctuation/special chars
    text = re.sub(r"\s+", " ", text).strip()
    return text

# --- Vectorize all known symptoms ---
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(symptoms)

def match_symptoms(user_input: str, top_k: int = 3):
    """Return top_k most similar symptoms to user input"""
    user_input = preprocess(user_input)
    user_vec = vectorizer.transform([user_input])
    sims = cosine_similarity(user_vec, tfidf_matrix).flatten()
    top_idx = sims.argsort()[-top_k:][::-1]
    results = [(symptoms[i], float(sims[i])) for i in top_idx]
    return results

# --- Test run ---
if __name__ == "__main__":
    while True:
        query = input("You: ")
        if query.lower() in ["exit","quit","bye"]:
            print("Bot: Goodbye! Stay healthy.")
            break
        matches = match_symptoms(query, top_k=3)
        print("Bot: Did you mean...")
        for sym, score in matches:
            print(f"  - {sym} (similarity {score:.2f})")
