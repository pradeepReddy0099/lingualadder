"""Multilingual difficulty model.

Training labels come for free: Simple English Wikipedia and Vikidia articles are
written for young readers / learners (easy = 1), regular Wikipedia articles are
not (easy = 0). Features are z-scored *within each language* so that the model
learns "harder than is typical for this language" and can transfer to
languages that have no easy edition (here Hindi and Japanese).
"""
from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .textproc import ALL_FEATURE_NAMES, FEATURE_NAMES, ext_features, features, words

BASE_DIM = len(FEATURE_NAMES)

RARE_TOP_K = 3000
EXTENDED = True    # base 8 features + extended features (see difficulty_exp.py)


def rare_vocab(texts, lang, k=RARE_TOP_K):
    """The language's k most frequent words (by document frequency) -> rank."""
    df = Counter()
    for t in texts:
        df.update({w.lower() for w in words(t[:6000], lang)})
    return {w: r for r, (w, _) in enumerate(df.most_common(k))}


def feature_matrix(docs_by_lang, extended=EXTENDED):
    """docs_by_lang: {lang: [doc,...]} -> (X, y, langs, flat_docs) with per-language z-scoring."""
    X_all, y_all, lang_all, flat = [], [], [], []
    for lang, docs in docs_by_lang.items():
        vocab = rare_vocab([d["text"] for d in docs], lang)
        X = np.array([features(d["text"], lang, vocab) + (ext_features(d["text"], lang, vocab) if extended else [])
                      for d in docs], dtype=float)
        mu, sd = X.mean(0), X.std(0) + 1e-9
        X = (X - mu) / sd
        X_all.append(X)
        y_all += [d.get("easy", 0) for d in docs]
        lang_all += [lang] * len(docs)
        flat += docs
    return np.vstack(X_all), np.array(y_all), np.array(lang_all), flat


def feature_names():
    return ALL_FEATURE_NAMES if EXTENDED else FEATURE_NAMES


def make_model():
    # Predict P(hard): we fit on "hard" = 1 - easy.
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))


def train(X, y_easy):
    m = make_model()
    m.fit(X, 1 - y_easy)
    return m


def level_of(score: float) -> str:
    if score < 0.35:
        return "beginner"
    if score < 0.65:
        return "intermediate"
    return "advanced"
