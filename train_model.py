# =============================================================================
# train_model.py — Machine Learning Training Pipeline
# Fake News Detection using TF-IDF + Logistic Regression
# =============================================================================

import os
import sys
import logging
import re
import string
import joblib
import pandas as pd
import numpy as np
import nltk

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR   = os.path.join(BASE_DIR, "model")

FAKE_CSV   = os.path.join(DATASET_DIR, "Fake.csv")
TRUE_CSV   = os.path.join(DATASET_DIR, "True.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
VECT_PATH  = os.path.join(MODEL_DIR, "vectorizer.pkl")
META_PATH  = os.path.join(MODEL_DIR, "metadata.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# NLTK setup — download required corpora quietly
# ---------------------------------------------------------------------------
def download_nltk_data():
    """Download required NLTK datasets if not already present."""
    resources = ["stopwords", "punkt", "wordnet"]
    for resource in resources:
        try:
            nltk.data.find(f"corpora/{resource}")
        except LookupError:
            logger.info(f"Downloading NLTK resource: {resource}")
            nltk.download(resource, quiet=True)

download_nltk_data()

from nltk.corpus import stopwords

STOP_WORDS = set(stopwords.words("english"))

# ---------------------------------------------------------------------------
# Text Preprocessing
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """
    Clean and normalize a news article text:
    1. Lowercase
    2. Remove URLs
    3. Remove HTML tags
    4. Remove punctuation and digits
    5. Remove stopwords
    6. Strip extra whitespace
    """
    if not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)

    # Remove HTML tags
    text = re.sub(r"<.*?>", "", text)

    # Remove punctuation and digits
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", " ", text)

    # Tokenise and remove stopwords
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]

    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_dataset() -> pd.DataFrame:
    """
    Load Fake.csv and True.csv, assign labels, merge and shuffle.
    Returns a clean DataFrame with columns: [text, label]
      label = 0 → Real news
      label = 1 → Fake news
    """
    logger.info("Loading datasets …")

    if not os.path.exists(FAKE_CSV):
        raise FileNotFoundError(
            f"Fake.csv not found at: {FAKE_CSV}\n"
            "Please place Fake.csv and True.csv inside the 'dataset/' folder."
        )
    if not os.path.exists(TRUE_CSV):
        raise FileNotFoundError(
            f"True.csv not found at: {TRUE_CSV}\n"
            "Please place Fake.csv and True.csv inside the 'dataset/' folder."
        )

    fake_df = pd.read_csv(FAKE_CSV)
    true_df = pd.read_csv(TRUE_CSV)

    logger.info(f"  Fake articles: {len(fake_df):,}")
    logger.info(f"  True articles: {len(true_df):,}")

    # Assign labels
    fake_df["label"] = 1   # 1 = Fake
    true_df["label"] = 0   # 0 = Real

    # Combine title + text for richer features
    def combine_text(df: pd.DataFrame) -> pd.Series:
        if "title" in df.columns and "text" in df.columns:
            return df["title"].fillna("") + " " + df["text"].fillna("")
        elif "text" in df.columns:
            return df["text"].fillna("")
        else:
            # Use first string column as fallback
            str_cols = df.select_dtypes(include="object").columns.tolist()
            return df[str_cols[0]].fillna("") if str_cols else pd.Series([""] * len(df))

    fake_df["combined"] = combine_text(fake_df)
    true_df["combined"] = combine_text(true_df)

    df = pd.concat(
        [fake_df[["combined", "label"]], true_df[["combined", "label"]]],
        ignore_index=True,
    )
    df = df.rename(columns={"combined": "text"})

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    logger.info(f"  Total samples: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------
def train() -> dict:
    """
    Full ML pipeline:
      1. Load & label data
      2. Preprocess text
      3. Train/test split
      4. TF-IDF vectorisation
      5. Logistic Regression training
      6. Evaluation
      7. Save model artefacts
    Returns metadata dict.
    """

    # 1. Load data
    df = load_dataset()

    # 2. Preprocess
    logger.info("Cleaning and preprocessing text (this may take a minute) …")
    df["clean_text"] = df["text"].apply(clean_text)

    # Drop empty rows
    df = df[df["clean_text"].str.strip().ne("")]

    X = df["clean_text"].values
    y = df["label"].values

    # 3. Train / test split  (80 / 20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

    # 4. TF-IDF vectorisation
    logger.info("Fitting TF-IDF vectorizer …")
    vectorizer = TfidfVectorizer(
        max_features=50_000,
        ngram_range=(1, 2),       # unigrams + bigrams
        sublinear_tf=True,        # apply log normalisation
        min_df=2,
        max_df=0.95,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf  = vectorizer.transform(X_test)

    # 5. Logistic Regression
    logger.info("Training Logistic Regression …")
    model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver="lbfgs",
        random_state=42,
    )
    model.fit(X_train_tfidf, y_train)

    # 6. Evaluation
    y_pred = model.predict(X_test_tfidf)
    accuracy = accuracy_score(y_test, y_pred)
    report   = classification_report(y_test, y_pred, target_names=["Real", "Fake"])
    cm       = confusion_matrix(y_test, y_pred).tolist()

    logger.info(f"\n{'='*50}")
    logger.info(f"  Model Accuracy: {accuracy * 100:.2f}%")
    logger.info(f"\n{report}")
    logger.info(f"  Confusion Matrix: {cm}")
    logger.info(f"{'='*50}\n")

    # 7. Save artefacts
    joblib.dump(model,      MODEL_PATH)
    joblib.dump(vectorizer, VECT_PATH)

    metadata = {
        "accuracy":          round(accuracy * 100, 2),
        "train_samples":     int(len(X_train)),
        "test_samples":      int(len(X_test)),
        "total_samples":     int(len(X_train) + len(X_test)),
        "fake_count":        int(np.sum(y == 1)),
        "real_count":        int(np.sum(y == 0)),
        "classification_report": report,
        "confusion_matrix":  cm,
        "model_path":        MODEL_PATH,
        "vectorizer_path":   VECT_PATH,
        "ngram_range":       "(1, 2)",
        "max_features":      50_000,
    }
    joblib.dump(metadata, META_PATH)

    logger.info(f"Model saved  → {MODEL_PATH}")
    logger.info(f"Vectorizer   → {VECT_PATH}")
    logger.info(f"Metadata     → {META_PATH}")

    return metadata


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = train()
    logger.info("Training complete!")
    logger.info(f"Final Accuracy: {result['accuracy']}%")
