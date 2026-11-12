"""Difficulty-model experiments: extra features x model families.

Compares, with the same 5-fold stratified CV and leave-one-language-out
protocol as evaluate.py:
  feature sets : base (8 original features) / base + extended features
  models       : logistic regression, calibrated LR (C tuned), gradient boosting

Usage: python -m lingualadder.difficulty_exp   (writes data/difficulty_exp.json)
"""
import json

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .build import LABELED, load_raw
from .config import DATA_DIR
from .difficulty import BASE_DIM, feature_matrix
from .textproc import ALL_FEATURE_NAMES


def models():
    return {
        "LR": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)),
        "LR_C0.1": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=0.1)),
        "GBT": lambda: HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                                      l2_regularization=1.0, random_state=0),
    }


def evaluate(X, y, langs, make):
    skf = StratifiedKFold(5, shuffle=True, random_state=0)
    pred, prob = np.zeros_like(y), np.zeros(len(y))
    for tr, te in skf.split(X, y):
        m = make().fit(X[tr], y[tr])
        prob[te] = m.predict_proba(X[te])[:, 1]
        pred[te] = (prob[te] >= 0.5).astype(int)
    out = {"cv_accuracy": round(accuracy_score(y, pred), 3), "cv_f1": round(f1_score(y, pred), 3),
           "cv_auc": round(roc_auc_score(y, prob), 3)}
    lolo = {}
    for held in LABELED:
        tr, te = langs != held, langs == held
        m = make().fit(X[tr], y[tr])
        p = m.predict(X[te])
        lolo[held] = round(accuracy_score(y[te], p), 3)
    out["lolo_accuracy"] = lolo
    out["lolo_mean"] = round(float(np.mean(list(lolo.values()))), 3)
    return out


def main():
    by_lang = {l: d for l, d in load_raw().items() if l in LABELED}
    X, y_easy, langs, _ = feature_matrix(by_lang, extended=True)
    y = 1 - y_easy
    sets = {"base": list(range(BASE_DIM)), "extended": list(range(X.shape[1]))}
    res = {"features": ALL_FEATURE_NAMES, "rows": []}
    for fs, cols in sets.items():
        for name, make in models().items():
            r = {"features": fs, "model": name, **evaluate(X[:, cols], y, langs, make)}
            print(r)
            res["rows"].append(r)
    (DATA_DIR / "difficulty_exp.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
