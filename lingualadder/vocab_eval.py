"""Evaluate vocabulary-aware re-ranking (the `known`/`beta` option in search()).

A simulated learner knows the N most frequent words of the language (frequency = number of
article openings containing the word). N = 300 / 1,500 / 5,000 for beginner / intermediate / advanced,
each searching at their level's target. For several beta values we measure, per language:
 - nDCG@10 and P@10 (same queries and relevance as evaluate.py)
 - known-word coverage: mean share of tokens in the top-10 snippets that the learner knows
 - readable share: share of top-10 snippets where >= 90% of tokens are known
Usage: python -m lingualadder.vocab_eval   (writes data/vocab_eval.json)
"""
import json
from collections import Counter
import numpy as np
from .config import DATA_DIR, LEVELS
from .evaluate import build_queries, ndcg
from .search import LinguaLadder
from .textproc import index_tokens

VOCAB = {"beginner": 300, "intermediate": 1500, "advanced": 5000}
BETAS = (0.0, 0.1, 0.3, 0.5, 1.0, 2.0)


def known_sets(eng, lang):
    df = Counter()
    for d in eng.docs[lang]:
        df.update(set(index_tokens(d["snippet"], lang)))
    ranked = [w for w, _ in df.most_common()]
    return {lvl: set(ranked[:n]) for lvl, n in VOCAB.items()}


def run(eng=None):
    eng = eng or LinguaLadder()
    qs_all = build_queries(eng)
    out = {}
    for lang, qs in qs_all.items():
        ks = known_sets(eng, lang)
        for level, cfg in LEVELS.items():
            known = ks[level]
            for beta in BETAS:
                agg = {"ndcg10": [], "p10": [], "coverage": [], "readable": []}
                for q, topic, n_rel in qs:
                    top = eng.search(lang, q, cfg["target"], known=known, beta=beta)
                    rels = [1 if r["topic"] == topic else 0 for r in top]
                    agg["ndcg10"].append(ndcg(rels, n_rel)); agg["p10"].append(sum(rels) / 10)
                    covs = []
                    for r in top:
                        toks = index_tokens(r["snippet"], lang)
                        covs.append(sum(t in known for t in toks) / len(toks) if toks else 0.0)
                    if covs:
                        agg["coverage"].append(float(np.mean(covs)))
                        agg["readable"].append(float(np.mean([c >= 0.9 for c in covs])))
                out[f"{lang}/{level}/beta{beta}"] = {k: round(float(np.mean(v)), 3) for k, v in agg.items()}
    summ = {}
    for lang in qs_all:
        for beta in BETAS:
            rows = [out[f"{lang}/{l}/beta{beta}"] for l in LEVELS]
            summ[f"{lang}/beta{beta}"] = {k: round(float(np.mean([r[k] for r in rows])), 3) for k in rows[0]}
    out["summary"] = summ
    (DATA_DIR / "vocab_eval.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    o = run()
    for k, v in o["summary"].items():
        print(k, v)
