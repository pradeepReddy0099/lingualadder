"""Graduate-level evaluation: baselines, ablations, paired significance tests.

Systems compared (same BM25 top-100 candidates, same fusion formula):
  BM25          relevance only
  Readability   level fit from a readability-formula model (sentence + word length only)
  LL-noRarity   full model minus the word-rarity feature (ablation)
  LinguaLadder  full model

Per query, metrics are averaged over the three learner levels. Significance:
paired two-sided randomization test (10,000 permutations) and Wilcoxon signed-rank,
LinguaLadder vs each other system, over queries.

Usage: python -m lingualadder.grad_eval
"""
import json, math
from collections import defaultdict
import numpy as np
from scipy.stats import wilcoxon
from .build import LABELED
from .config import ALPHA, DATA_DIR, LEVELS, MODEL_DIR, SIGMA
from .difficulty import BASE_DIM, feature_names, make_model
from .evaluate import BAND, build_queries, ndcg
from .search import LinguaLadder

rng = np.random.default_rng(0)


def alt_difficulties(engine, cols):
    X = np.load(MODEL_DIR / "features.npy")
    langs, easy = [], []
    for l, docs in engine.docs.items():
        for d in docs:
            langs.append(l); easy.append(d["easy"])
    langs, y = np.array(langs), 1 - np.array(easy)
    m = np.isin(langs, list(LABELED))
    model = make_model().fit(X[m][:, cols], y[m])
    p = model.predict_proba(X[:, cols])[:, 1]
    out, i = {}, 0
    for l, docs in engine.docs.items():
        for d in docs:
            out[(l, d["id"])] = float(p[i]); i += 1
    return out


def run(engine, lang, q, topic, n_rel, t, diff):
    cands = engine.bm25(lang, q)
    if not cands:
        return 0, 0, 0, None
    top = cands[0][1] or 1.0
    rows = []
    for i, s in cands:
        d = engine.docs[lang][i]
        rel = s / top
        if diff is None:
            score = rel
        else:
            dd = diff[(lang, d["id"])] if diff != "full" else d["difficulty"]
            score = ALPHA * rel + (1 - ALPHA) * math.exp(-((dd - t) ** 2) / (2 * SIGMA ** 2))
        rows.append((score, d))
    rows.sort(key=lambda r: -r[0])
    top10 = [d for _, d in rows[:10]]
    rels = [1 if d["topic"] == topic else 0 for d in top10]
    # level match always judged with the full model's difficulty (the reference estimate)
    lm = sum(1 for d in top10 if abs(d["difficulty"] - t) <= BAND) / max(len(top10), 1)
    # independent check: source label (Simple/Vikidia = easy) for beginner and advanced targets
    if t <= 0.2:
        gold = sum(d["easy"] for d in top10) / max(len(top10), 1)
    elif t >= 0.8:
        gold = sum(1 - d["easy"] for d in top10) / max(len(top10), 1)
    else:
        gold = None
    return sum(rels) / 10, ndcg(rels, n_rel), lm, gold


def perm_test(a, b, n=10000):
    d = np.array(a) - np.array(b)
    obs = abs(d.mean())
    signs = rng.choice([-1, 1], size=(n, len(d)))
    return float(((np.abs((signs * d).mean(1))) >= obs).mean())


def main():
    eng = LinguaLadder()
    names = feature_names()
    fi = names.index
    rarity = {n for n in names if n in ("rare_word_share", "core_vocab_share", "mid_band_share")}
    systems = {
        "BM25": None,
        "Readability": alt_difficulties(eng, [fi("avg_sentence_len"), fi("avg_word_len")]),
        "LL-noRarity": alt_difficulties(eng, [i for i, n in enumerate(names) if n not in rarity]),
    }
    if len(names) > BASE_DIM:
        systems["LL-8feat"] = alt_difficulties(eng, list(range(BASE_DIM)))
    systems["LinguaLadder"] = "full"
    queries = build_queries(eng)
    results = {}
    for scope, langs in (("en_es", ["en", "es"]), ("labeled", ["en", "es"]), ("all", list(queries))):
        per = {s: defaultdict(list) for s in systems}
        for lang in langs:
            for q, topic, n_rel in queries[lang]:
                for s, diff in systems.items():
                    out = [run(eng, lang, q, topic, n_rel, c["target"], diff) for c in LEVELS.values()]
                    vals = np.array([o[:3] for o in out])
                    for k, v in zip(("p10", "ndcg10", "level_match"), vals.mean(0)):
                        per[s][k].append(float(v))
                    g = [o[3] for o in out if o[3] is not None]
                    per[s]["gold_level"].append(float(np.mean(g)))
        summ = {s: {k: round(float(np.mean(v)), 3) for k, v in m.items()} for s, m in per.items()}
        tests = {}
        for s in systems:
            if s == "LinguaLadder":
                continue
            tests[s] = {}
            for k in ("ndcg10", "level_match", "gold_level"):
                a, b = per["LinguaLadder"][k], per[s][k]
                try:
                    w = float(wilcoxon(a, b).pvalue)
                except ValueError:
                    w = 1.0
                tests[s][k] = {"diff": round(float(np.mean(a) - np.mean(b)), 3),
                               "perm_p": perm_test(a, b), "wilcoxon_p": w}
        results[scope] = {"n_queries": len(per["BM25"]["p10"]), "summary": summ, "tests_vs_LL": tests}
    (DATA_DIR / "grad_eval.json").write_text(json.dumps(results, indent=1))
    print(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
