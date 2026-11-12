"""Build step: clean corpus -> difficulty model -> BM25 indexes.

Usage:  python -m lingualadder.build
Reads data/raw/*.jsonl, writes data/corpus.jsonl, data/models/difficulty.pkl,
data/index.pkl
"""
import json
import pickle
from collections import defaultdict

import numpy as np

from .config import DATA_DIR, LANGUAGES, MODEL_DIR, RAW_DIR
from .difficulty import feature_matrix, level_of, train
from .search import BM25Index
from .textproc import index_tokens, sentences, strip_headings, words

LABELED = {"en", "es"}


def load_raw():
    by_lang = defaultdict(list)
    seen = set()
    for path in sorted(RAW_DIR.glob("*.jsonl")):
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            key = (d["source"], d["pageid"])
            if key in seen or d["lang"] not in LANGUAGES:
                continue
            seen.add(key)
            by_lang[d["lang"]].append(d)
    return by_lang


def snippet(text, n=220):
    body = " ".join(strip_headings(text).split())
    return body[:n] + ("…" if len(body) > n else "")


def main():
    by_lang = load_raw()
    for lang, docs in by_lang.items():
        e = sum(d["easy"] for d in docs)
        print(f"{lang}: {len(docs)} docs ({e} easy, {len(docs) - e} regular)")

    X, y, langs, flat = feature_matrix(by_lang)
    mask = np.isin(langs, list(LABELED))
    model = train(X[mask], y[mask])
    probs = model.predict_proba(X)[:, 1]
    with open(MODEL_DIR / "difficulty.pkl", "wb") as f:
        pickle.dump(model, f)
    np.save(MODEL_DIR / "features.npy", X)

    docs_out = defaultdict(list)
    for d, p, lang in zip(flat, probs, langs):
        doc = {
            "id": f"{d['source']}:{d['pageid']}", "lang": lang, "title": d["title"], "url": d["url"],
            "source": d["source"], "topic": d.get("topic"), "en_title": d.get("en_title"),
            "easy": d["easy"], "difficulty": round(float(p), 4), "level": level_of(float(p)),
            "text": d["text"], "snippet": snippet(d["text"]), "words": len(words(d["text"], lang)),
            "sentences": len(sentences(d["text"])),
        }
        docs_out[lang].append(doc)

    with open(DATA_DIR / "corpus.jsonl", "w", encoding="utf-8") as f:
        for lang in docs_out:
            for doc in docs_out[lang]:
                f.write(json.dumps({k: v for k, v in doc.items()}, ensure_ascii=False) + "\n")

    indexes = {}
    for lang, docs in docs_out.items():
        # Title is repeated so title matches count more.
        indexes[lang] = BM25Index().build([index_tokens((d["title"] + " ") * 3 + d["text"], lang) for d in docs])
        lv = defaultdict(int)
        for d in docs:
            lv[d["level"]] += 1
        print(f"  indexed {lang}: {len(docs)} docs, {len(indexes[lang].idf)} terms, levels {dict(lv)}")

    with open(DATA_DIR / "index.pkl", "wb") as f:
        pickle.dump({"docs": dict(docs_out), "indexes": indexes}, f)
    print("Build complete.")


if __name__ == "__main__":
    main()
