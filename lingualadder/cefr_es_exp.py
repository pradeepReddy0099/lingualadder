"""Spanish CEFR head experiment with the CAES learner corpus (UniversalCEFR/caes_es, A1-C1, 31k essays).

Questions (all Spanish):
  1. does the production difficulty score rank CAES essays by CEFR level (Spearman)?
  2. does a ridge head on the 15 features transfer BETWEEN sources (train CAES -> test Kwiziq, train Kwiziq -> test CAES)?
  3. does it still put Vikidia (easy) articles below Wikipedia articles, i.e. does it transfer to long articles?
Writes data/cefr_es_exp.json. Usage: python -m lingualadder.cefr_es_exp
"""
import json
import pickle
import random
import urllib.request

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge

from .cefr_validate import ORDER, corpus_stats, fetch, level_idx
from .config import DATA_DIR, MODEL_DIR
from .textproc import ext_features, features

CAES_URL = "https://huggingface.co/datasets/UniversalCEFR/caes_es/resolve/main/caes.json"
PER_LEVEL = 500


def caes_sample(seed=0):
    path = DATA_DIR / "external" / "caes.json"
    if not path.exists():
        urllib.request.urlretrieve(CAES_URL, path)
    rows = [r for r in json.load(open(path, encoding="utf-8")) if len(r["text"].split()) >= 40 and level_idx(r["cefr_level"]) is not None]
    rng = random.Random(seed)
    out = []
    for lab in ORDER:
        pool = [r for r in rows if r["cefr_level"] == lab]
        rng.shuffle(pool)
        out += [(r["text"], level_idx(lab)) for r in pool[:PER_LEVEL]]
    return out


def feats(texts, stats):
    vocab, mu, sd = stats
    return (np.array([features(t, "es", vocab) + ext_features(t, "es", vocab) for t in texts], float) - mu) / sd


def main():
    model = pickle.load(open(MODEL_DIR / "difficulty.pkl", "rb"))
    stats = corpus_stats("es")
    caes = caes_sample()
    kw = [(r["text"], level_idx(r["cefr_level"])) for r in fetch("kwiziq") if len(r["text"].split()) >= 15 and level_idx(r["cefr_level"]) is not None]
    Xc, yc = feats([t for t, _ in caes], stats), np.array([y for _, y in caes])
    Xk, yk = feats([t for t, _ in kw], stats), np.array([y for _, y in kw])
    res = {"n_caes": len(yc), "n_kwiziq": len(yk)}
    cur_c = model.predict_proba(Xc)[:, 1]
    cur_k = model.predict_proba(Xk)[:, 1]
    res["current_score_spearman"] = {"caes": round(float(spearmanr(cur_c, yc).correlation), 3), "kwiziq": round(float(spearmanr(cur_k, yk).correlation), 3)}
    res["caes_median_score_by_level"] = {ORDER[i]: round(float(np.median(cur_c[yc == i])), 3) for i in sorted(set(yc))}
    # transfer between sources
    for alpha in (10.0,):
        h_c = Ridge(alpha=alpha).fit(Xc, yc)
        h_k = Ridge(alpha=alpha).fit(Xk, yk)
        res["head_trained_caes_test_kwiziq_spearman"] = round(float(spearmanr(h_c.predict(Xk), yk).correlation), 3)
        res["head_trained_kwiziq_test_caes_spearman"] = round(float(spearmanr(h_k.predict(Xc), yc).correlation), 3)
        both = Ridge(alpha=alpha).fit(np.vstack([Xc, Xk]), np.concatenate([yc, yk]))
    # cross-validated on CAES alone
    idx = np.random.RandomState(0).permutation(len(yc)); h = len(yc) // 2
    hh = Ridge(alpha=10.0).fit(Xc[idx[:h]], yc[idx[:h]])
    res["head_caes_half_split_spearman"] = round(float(spearmanr(hh.predict(Xc[idx[h:]]), yc[idx[h:]]).correlation), 3)
    # fully out-of-source band accuracy: cuts matched to CAES level shares, applied to Kwiziq documents and Habla Cultura paragraphs
    hc = [(r["text"], level_idx(r["cefr_level"])) for r in fetch("hablacultura") if len(r["text"].split()) >= 15 and level_idx(r["cefr_level"]) is not None]
    Xh, yh = feats([t for t, _ in hc], stats), np.array([y for _, y in hc])
    props = np.cumsum([(yc == i).mean() for i in range(5)])[:-1]
    res["band_transfer_cuts_from_caes"] = {}
    for name, f in (("production_score", lambda X: model.predict_proba(X)[:, 1]), ("head_caes", h_c.predict)):
        cuts = np.quantile(f(Xc), props)
        row = {}
        for tag, X, y in (("kwiziq", Xk, yk), ("hablacultura", Xh, yh)):
            pred = np.searchsorted(cuts, f(X), side="right")
            row[tag] = {"spearman": round(float(spearmanr(f(X), y).correlation), 3), "exact": round(float((pred == y).mean()), 3), "within1": round(float((abs(pred - y) <= 1).mean()), 3)}
        res["band_transfer_cuts_from_caes"][name] = row
    # long articles: Vikidia vs Wikipedia in the Spanish corpus
    rng = random.Random(1)
    docs = [json.loads(l) for l in open(DATA_DIR / "corpus.jsonl", encoding="utf-8")]
    docs = [d for d in docs if d["lang"] == "es"]
    vik = [d["text"] for d in docs if d["source"] == "es.vikidia"]
    wik = [d["text"] for d in docs if d["source"] == "es.wikipedia"]
    rng.shuffle(vik); rng.shuffle(wik)
    Xv, Xw = feats(vik[:600], stats), feats(wik[:600], stats)
    res["articles"] = {}
    for name, f in (("production_score", lambda X: model.predict_proba(X)[:, 1]), ("head_caes", h_c.predict), ("head_kwiziq", h_k.predict), ("head_both", both.predict)):
        v, w = f(Xv), f(Xw)
        # AUC: P(random Wikipedia article scores above a random Vikidia article)
        auc = float(np.mean([(w > x).mean() + 0.5 * (w == x).mean() for x in v[:300]]))
        res["articles"][name] = {"vikidia_median": round(float(np.median(v)), 3), "wikipedia_median": round(float(np.median(w)), 3), "auc_wiki_above_vikidia": round(auc, 3)}
    # the A1-C1 index of the two sources by the caes head, to see where long articles land
    res["head_caes_article_index_pctiles"] = {"vikidia": [round(float(x), 2) for x in np.percentile(h_c.predict(Xv), [10, 50, 90])],
                                              "wikipedia": [round(float(x), 2) for x in np.percentile(h_c.predict(Xw), [10, 50, 90])]}
    json.dump(res, open(DATA_DIR / "cefr_es_exp.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
