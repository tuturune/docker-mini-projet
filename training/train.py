"""Entraîne les deux versions du modèle d'analyse de sentiment.

Jeu de données : avis de films Allociné (https://huggingface.co/datasets/tblard/allocine).

    python training/train.py --data-dir /chemin/vers/parquet --out-dir models

- v1 : modèle volontairement simple (sac de mots + Naive Bayes, 20 000 avis).
- v2 : modèle plus précis (TF-IDF mots et bigrammes + régression logistique, tous les avis).
"""

import argparse
import datetime as dt
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

LABELS = {0: "negatif", 1: "positif"}


def build_v1() -> Pipeline:
    return Pipeline(
        [
            ("vect", CountVectorizer(lowercase=True, max_features=5000, binary=True)),
            ("clf", MultinomialNB()),
        ]
    )


def build_v2() -> Pipeline:
    return Pipeline(
        [
            (
                "vect",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=3,
                    max_features=100_000,
                    sublinear_tf=True,
                ),
            ),
            ("clf", LogisticRegression(C=4.0, max_iter=1000)),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--out-dir", default=Path("models"), type=Path)
    args = parser.parse_args()

    train = pd.read_parquet(args.data_dir / "train.parquet")
    test = pd.read_parquet(args.data_dir / "test.parquet")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    versions = {
        "v1": (build_v1(), train.sample(20_000, random_state=42)),
        "v2": (build_v2(), train),
    }
    for version, (pipeline, data) in versions.items():
        pipeline.fit(data["review"], data["label"])
        accuracy = accuracy_score(test["label"], pipeline.predict(test["review"]))
        artifact = {
            "version": version,
            "pipeline": pipeline,
            "labels": LABELS,
            "accuracy": round(float(accuracy), 4),
            "trained_at": dt.date.today().isoformat(),
            "train_size": len(data),
        }
        path = args.out_dir / f"sentiment-{version}.joblib"
        joblib.dump(artifact, path, compress=3)
        size_mb = path.stat().st_size / 1_000_000
        print(f"{version}: accuracy={accuracy:.4f} taille={size_mb:.1f} Mo -> {path}")


if __name__ == "__main__":
    main()
