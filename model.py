print("🚀 Training script started...")
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
import os


# Paths
DATA_PATH = os.path.join("data", "intents.csv")
MODEL_PATH = "model.pkl"


def train_model():
    # Load dataset
    df = pd.read_csv(DATA_PATH)

    # Build pipeline (TF-IDF + Naive Bayes Classifier)
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())

    # Train
    model.fit(df["query"], df["intent"])

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Model trained and saved at {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
