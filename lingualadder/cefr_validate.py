"""Validate the difficulty score and the A1-C2 bands against externally CEFR-labelled texts.

Data (UniversalCEFR, downloaded once into data/external/, not committed):
  en: Cambridge exam reading texts (A2-C2, 331 docs) + ELG CEFR (A1-C2, 712 docs)
  es: Kwiziq reading texts (A1-C1, 206 docs) + Habla Cultura paragraphs (A2-C1, 713, paragraph level)
Method: score every text with the production difficulty model, z-scoring the features with the
corpus statistics of its own language (exactly what build.py does for corpus articles).
Reports Spearman correlation, accuracy of the current bands, and bands re-fit on half of the texts
and tested on the other half. Writes data/cefr_validation.json.

Usage: python -m lingualadder.cefr_validate [--fit]
"""
import json
import pickle
import sys
import urllib.request
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import spearmanr

from .config import DATA_DIR, MODEL_DIR
from .difficulty import rare_vocab
from .search import CEFR_CUTS, cefr_label

OLD_BANDS = [(0.20, 'A1'), (0.61, 'A2'), (0.87, 'B1'), (0.94, 'B2'), (0.98, 'C1'), (1.01, 'C2')]  # corpus-quantile bands used before validation
from .textproc import ext_features, features

EXT_DIR = DATA_DIR / "external"
BASE = "https://huggingface.co/datasets/UniversalCEFR"
SOURCES = {  # name -> (repo, file, lang, granularity)
    "cambridge": ("cambridge_exams_en", "cambridge_exams.json", "en", "document"),
    "elg": ("elg_cefr_en", "elg-cefr-en.json", "en", "document"),
    "kwiziq": ("kwiqiz_es", "kwiziq-es.json", "es", "document"),
    "hablacultura": ("hablacultura_es", "hablacultura.json", "es", "paragraph"),
}
ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def fetch(name):
    repo, fname, _, _ = SOURCES[name]
    EXT_DIR.mkdir(exist_ok=True)
    path = EXT_DIR / fname
    if not path.exists():
        urllib.request.urlretrieve(f"{BASE}/{repo}/resolve/main/{fname}", path)
    return json.load(open(path, encoding="utf-8"))


def level_idx(lab):
    lab = lab.rstrip("+")
    return ORDER.index(lab) if lab in ORDER else None


def corpus_stats(lang):
    """vocab, mean, sd of the corpus feature matrix, as in difficulty.feature_matrix."""
    docs = [json.loads(l) for l in open(DATA_DIR / "corpus.jsonl", encoding="utf-8")]
    docs = [d for d in docs if d["lang"] == lang]
    vocab = rare_vocab([d["text"] for d in docs], lang)
    X = np.array([features(d["text"], lang, vocab) + ext_features(d["text"], lang, vocab) for d in docs], float)
    return vocab, X.mean(0), X.std(0) + 1e-9


def score(texts, lang, stats, model):
    vocab, mu, sd = stats
    X = np.array([features(t, lang, vocab) + ext_features(t, lang, vocab) for t in texts], float)
    return model.predict_proba((X - mu) / sd)[:, 1]


def band_fn(cuts):
    def f(d):
        for hi, lab in cuts:
            if d < hi:
                return lab
        return cuts[-1][1]
    return f


def fit_cuts(d, y, labels):
    """Monotone cutpoints between the observed CEFR levels that maximise exact accuracy (greedy coordinate search)."""
    d = np.asarray(d); y = np.asarray(y)
    qs = np.quantile(d, np.linspace(0.02, 0.98, 49))
    k = len(labels)
    cuts = list(np.quantile(d, np.linspace(0, 1, k + 1)[1:-1]))

    def acc(c):
        pred = np.searchsorted(np.array(c), d, side="right")
        return float((pred == y).mean())
    best = acc(cuts)
    for _ in range(6):
        for i in range(len(cuts)):
            lo = cuts[i - 1] if i else -1
            hi = cuts[i + 1] if i + 1 < len(cuts) else 2
            for q in qs:
                if lo < q < hi:
                    c2 = cuts[:i] + [q] + cuts[i + 1:]
                    a = acc(c2)
                    if a > best + 1e-12:
                        best, cuts = a, c2
    return cuts, best


def main():
    model = pickle.load(open(MODEL_DIR / "difficulty.pkl", "rb"))
    out = {"sources": {}, "languages": {}}
    per_lang = defaultdict(lambda: {"d": [], "y": [], "src": []})
    stats = {}
    for name, (_, _, lang, gran) in SOURCES.items():
        if lang not in stats:
            stats[lang] = corpus_stats(lang)
        rows = [(r["text"], level_idx(r["cefr_level"])) for r in fetch(name)]
        rows = [(t, y) for t, y in rows if y is not None and len(t.split()) >= 15]
        texts, ys = zip(*rows)
        d = score(texts, lang, stats[lang], model)
        rho = spearmanr(d, ys).correlation
        by = {ORDER[i]: round(float(np.median(d[np.array(ys) == i])), 3) for i in sorted(set(ys))}
        cur = [ORDER.index(cefr_label(x, lang)) for x in d]
        old = [ORDER.index(band_fn(OLD_BANDS)(x)) for x in d]
        exact = float(np.mean([c == y for c, y in zip(cur, ys)]))
        within1 = float(np.mean([abs(c - y) <= 1 for c, y in zip(cur, ys)]))
        out["sources"][name] = {"lang": lang, "granularity": gran, "n": len(ys), "spearman": round(float(rho), 3),
                                "median_difficulty_by_level": by, "levels": dict(Counter(ORDER[y] for y in ys)),
                                "shipped_bands_exact": round(exact, 3), "shipped_bands_within1": round(within1, 3),
                                "old_bands_exact": round(float(np.mean([c == y for c, y in zip(old, ys)])), 3),
                                "old_bands_within1": round(float(np.mean([abs(c - y) <= 1 for c, y in zip(old, ys)])), 3)}
        o = out["sources"][name]
        print(f"{name:13s} {lang} {gran:9s} n={len(ys):4d} spearman={rho:.3f} shipped bands exact={exact:.3f} within1={within1:.3f} "
              f"(old bands exact {o['old_bands_exact']:.3f} within1 {o['old_bands_within1']:.3f}) medians={by}")
        if gran == "document":
            pl = per_lang[lang]
            pl["d"] += list(d); pl["y"] += list(ys); pl["src"] += [name] * len(ys)

    for lang, pl in per_lang.items():
        d, y = np.array(pl["d"]), np.array(pl["y"])
        rho = spearmanr(d, y).correlation
        used = sorted(set(y))
        yt = np.array([used.index(v) for v in y])
        res = {"quantile": [], "old": [], "majority": []}
        for seed in range(10):  # 10 random half/half splits: cuts from one half, accuracy on the other
            idx = np.random.RandomState(seed).permutation(len(y)); h = len(y) // 2
            tr, te = idx[:h], idx[h:]
            props = np.cumsum([(yt[tr] == i).mean() for i in range(len(used))])[:-1]
            pred = np.searchsorted(np.quantile(d[tr], props), d[te], side="right")
            res["quantile"].append(((pred == yt[te]).mean(), (abs(pred - yt[te]) <= 1).mean()))
            old = np.array([ORDER.index(band_fn(OLD_BANDS)(x)) for x in d[te]])
            res["old"].append(((old == y[te]).mean(), (abs(old - y[te]) <= 1).mean()))
            m = Counter(yt[tr]).most_common(1)[0][0]
            res["majority"].append(((yt[te] == m).mean(), (abs(yt[te] - m) <= 1).mean()))
        full = np.cumsum([(yt == i).mean() for i in range(len(used))])[:-1]
        cuts = [round(float(c), 3) for c in np.quantile(d, full)]
        summ = {k: {"exact": round(float(np.mean([a for a, _ in v])), 3), "within1": round(float(np.mean([b for _, b in v])), 3)}
                for k, v in res.items()}
        out["languages"][lang] = {"n": int(len(y)), "levels": [ORDER[u] for u in used], "spearman": round(float(rho), 3),
                                  "heldout_mean_of_10_splits": summ, "cuts_fitted_on_all": cuts, "cuts_shipped": CEFR_CUTS[lang]}
        print(f"[{lang}] n={len(y)} levels={[ORDER[u] for u in used]} spearman={rho:.3f}; held-out (10 half splits): "
              f"quantile-matched bands exact {summ['quantile']['exact']:.3f} within1 {summ['quantile']['within1']:.3f} | "
              f"old bands exact {summ['old']['exact']:.3f} within1 {summ['old']['within1']:.3f} | "
              f"always-majority exact {summ['majority']['exact']:.3f} within1 {summ['majority']['within1']:.3f}; cuts {cuts}")
    json.dump(out, open(DATA_DIR / "cefr_validation.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
