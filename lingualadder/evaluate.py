"""Evaluation for the proposal's three questions.

1. Difficulty model: accuracy / F1 on easy vs. regular articles
   - 5-fold cross-validation on the labeled languages (en, es, fr)
   - leave-one-language-out: train on two languages, test on the third
   - baseline: only sentence length + word length (a readability-formula-like model)
2. Retrieval quality: Precision@10 and nDCG@10. Queries are the seed topics written
   in each language (the seed article's own title there). An article is relevant if
   it was collected for that topic.
3. Level match: share of the top 10 whose difficulty is within 0.15 of the learner's
   target, for plain BM25 vs. LinguaLadder re-ranking, for every level.

Usage: python -m lingualadder.evaluate   (writes data/eval_results.json and data/eval_report.md)
"""
import json
import math
from collections import defaultdict

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold

from .build import LABELED, load_raw
from .config import ALPHA, DATA_DIR, LEVELS, SIGMA
from .difficulty import feature_matrix, feature_names, make_model
from .search import LinguaLadder
from .textproc import FEATURE_NAMES

BAND = 0.15


def classifier_eval():
    by_lang = {l: d for l, d in load_raw().items() if l in LABELED}
    X, y_easy, langs, _ = feature_matrix(by_lang)
    y = 1 - y_easy  # 1 = hard
    out = {"n": int(len(y)), "per_language": {l: int((langs == l).sum()) for l in LABELED}}
    base_cols = [FEATURE_NAMES.index("avg_sentence_len"), FEATURE_NAMES.index("avg_word_len")]

    def cv(cols):
        skf = StratifiedKFold(5, shuffle=True, random_state=0)
        pred = np.zeros_like(y)
        for tr, te in skf.split(X, y):
            m = make_model().fit(X[tr][:, cols], y[tr])
            pred[te] = m.predict(X[te][:, cols])
        return {"accuracy": round(accuracy_score(y, pred), 3), "f1": round(f1_score(y, pred), 3)}

    all_cols = list(range(X.shape[1]))
    out["cv_full"] = cv(all_cols)
    out["cv_baseline"] = cv(base_cols)

    lolo = {}
    for held in LABELED:
        tr, te = langs != held, langs == held
        row = {}
        for name, cols in (("full", all_cols), ("baseline", base_cols)):
            m = make_model().fit(X[tr][:, cols], y[tr])
            p = m.predict(X[te][:, cols])
            row[name] = {"accuracy": round(accuracy_score(y[te], p), 3), "f1": round(f1_score(y[te], p), 3)}
        lolo[held] = row
    out["leave_one_language_out"] = lolo

    m = make_model().fit(X, y)
    coefs = m[-1].coef_[0]
    out["feature_weights"] = {n: round(float(c), 3) for n, c in sorted(zip(feature_names(), coefs), key=lambda x: -abs(x[1]))}
    return out


def ndcg(rels, n_relevant, k=10):
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels[:k]))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, n_relevant)))
    return dcg / ideal if ideal else 0.0


def build_queries(engine):
    """Each seed topic's title in each language becomes a query."""
    queries = defaultdict(list)
    for lang, docs in engine.docs.items():
        for d in docs:
            if d.get("topic") and d.get("en_title") == d["topic"] and not d["easy"]:
                n_rel = sum(1 for x in docs if x.get("topic") == d["topic"])
                if n_rel >= 5:
                    queries[lang].append((d["title"], d["topic"], n_rel))
    return queries


def retrieval_eval(engine, alpha=ALPHA, sigma=SIGMA, min_rel=0.0):
    queries = build_queries(engine)
    res = {}
    for lang, qs in queries.items():
        res[lang] = {"queries": len(qs)}
        for level, cfg in LEVELS.items():
            t = cfg["target"]
            agg = defaultdict(list)
            for q, topic, n_rel in qs:
                for name, rerank in (("bm25", False), ("lingualadder", True)):
                    top = engine.search(lang, q, t, alpha=alpha, sigma=sigma, rerank=rerank, min_rel=min_rel)
                    rels = [1 if r["topic"] == topic else 0 for r in top]
                    agg[f"{name}_p10"].append(sum(rels) / 10)
                    agg[f"{name}_ndcg10"].append(ndcg(rels, n_rel))
                    agg[f"{name}_level_match"].append(
                        sum(1 for r in top if abs(r["difficulty"] - t) <= BAND) / max(len(top), 1))
            res[lang][level] = {k: round(float(np.mean(v)), 3) for k, v in agg.items()}
    return res


def summarize(ret):
    keys = ["p10", "ndcg10", "level_match"]
    tot = {f"{m}_{k}": [] for m in ("bm25", "lingualadder") for k in keys}
    for lang, r in ret.items():
        for level in LEVELS:
            for k in tot:
                tot[k].append(r[level][k])
    return {k: round(float(np.mean(v)), 3) for k, v in tot.items()}


def alpha_sweep(engine):
    rows = []
    for a in (1.0, 0.8, 0.6, 0.5, 0.4, 0.2):
        s = summarize(retrieval_eval(engine, alpha=a))
        rows.append({"alpha": a, "p10": s["lingualadder_p10"], "ndcg10": s["lingualadder_ndcg10"],
                     "level_match": s["lingualadder_level_match"]})
    return rows


def main():
    engine = LinguaLadder()
    print("Evaluating difficulty model ...")
    clf = classifier_eval()
    print(json.dumps(clf, indent=1))
    print("Evaluating retrieval ...")
    ret = retrieval_eval(engine)
    summ = summarize(ret)
    print(json.dumps(summ, indent=1))
    print("Alpha sweep ...")
    sweep = alpha_sweep(engine)
    results = {"classifier": clf, "retrieval": ret, "retrieval_summary": summ, "alpha_sweep": sweep,
               "corpus": {l: len(d) for l, d in engine.docs.items()}}
    (DATA_DIR / "eval_results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))

    L = ["# LinguaLadder evaluation", ""]
    L += ["## Corpus", "", "| Language | Articles |", "|---|---|"]
    L += [f"| {l} | {n} |" for l, n in results["corpus"].items()]
    L += ["", "## 1. Difficulty model (easy vs. regular)", "",
          "| Setting | Accuracy | F1 |", "|---|---|---|",
          f"| 5-fold CV, all features | {clf['cv_full']['accuracy']} | {clf['cv_full']['f1']} |",
          f"| 5-fold CV, baseline (sentence + word length) | {clf['cv_baseline']['accuracy']} | {clf['cv_baseline']['f1']} |"]
    for held, r in clf["leave_one_language_out"].items():
        L.append(f"| Test on unseen language: {held}, all features | {r['full']['accuracy']} | {r['full']['f1']} |")
        L.append(f"| Test on unseen language: {held}, baseline | {r['baseline']['accuracy']} | {r['baseline']['f1']} |")
    L += ["", "Feature weights (positive = harder): " + ", ".join(f"{k} {v}" for k, v in clf["feature_weights"].items())]
    L += ["", "## 2-3. Retrieval and level match (top 10, averaged over levels)", "",
          "| Language | Queries | Level | P@10 BM25 | P@10 LL | nDCG@10 BM25 | nDCG@10 LL | Level match BM25 | Level match LL |",
          "|---|---|---|---|---|---|---|---|---|"]
    for lang, r in ret.items():
        for level in LEVELS:
            x = r[level]
            L.append(f"| {lang} | {r['queries']} | {level} | {x['bm25_p10']} | {x['lingualadder_p10']} | "
                     f"{x['bm25_ndcg10']} | {x['lingualadder_ndcg10']} | {x['bm25_level_match']} | {x['lingualadder_level_match']} |")
    L += ["", f"**Overall:** P@10 {summ['bm25_p10']} → {summ['lingualadder_p10']}, nDCG@10 {summ['bm25_ndcg10']} → "
          f"{summ['lingualadder_ndcg10']}, level match {summ['bm25_level_match']} → {summ['lingualadder_level_match']} (BM25 → LinguaLadder)."]
    L += ["", "## Alpha sweep (alpha = weight on relevance)", "", "| alpha | P@10 | nDCG@10 | Level match |", "|---|---|---|---|"]
    L += [f"| {r['alpha']} | {r['p10']} | {r['ndcg10']} | {r['level_match']} |" for r in sweep]
    (DATA_DIR / "eval_report.md").write_text("\n".join(L), encoding="utf-8")
    print("Wrote data/eval_report.md")


if __name__ == "__main__":
    main()
