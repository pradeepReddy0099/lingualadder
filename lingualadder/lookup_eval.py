"""Evaluate what looked-up ("new word") marks are worth when a learner picked the wrong level.

A simulated learner really knows the N most frequent words of the language (N = 300 / 1,500 / 5,000 for
beginner / intermediate / advanced, "true level") but declared a level ("declared level", possibly a different
one), so the search starts from that level's target difficulty and assumed known words. In a session of 30 topic
queries the learner reads the top result's snippet and marks up to MAXMARK words they do not know.
Arms:
  fixed   - nothing is learned from the session (declared target, declared known set)
  marks   - marked words leave the known set (what the app does since W8/W9)
  adapt   - marks plus a difficulty nudge: if the share of unknown words in the top snippet is above HARD
            the target goes down by STEP; if it is below EASY it goes up by STEP (a learner who marks
            nothing is not asked anything, so EASY needs the 'too easy' button in the real app)
  hard    - like adapt but only the downward nudge (what lookups alone can tell us)
Measured over the whole session and over the last 10 queries, per language: nDCG@10 (same relevance as
evaluate.py), known-word coverage of the top-10 snippets under the TRUE vocabulary, readable share (>= 90% known).
Usage: python -m lingualadder.lookup_eval   (writes data/lookup_eval.json)
"""
import json
import numpy as np
from .config import DATA_DIR, LEVELS
from .evaluate import build_queries, ndcg
from .search import LinguaLadder, adapt_target
from .textproc import index_tokens
from .vocab import known_set

HARD, EASY, STEP, MAXMARK, N_Q = 0.20, 0.03, 0.07, 5, 30


def session(eng, lang, qs, true_lvl, decl_lvl, arm, ranked, seed):
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(qs))[:N_Q]
    true_known = known_set(ranked, true_lvl, lang=lang)
    marked, target = [], LEVELS[decl_lvl]["target"]
    rows = []
    for i in order:
        q, topic, n_rel = qs[i]
        known = known_set(ranked, decl_lvl, marked, lang)
        top = eng.search(lang, q, target, known=known if arm != "fixed" else known_set(ranked, decl_lvl, (), lang))
        if not top:
            continue
        rels = [1 if r["topic"] == topic else 0 for r in top]
        covs = []
        for r in top:
            t = index_tokens(r["snippet"], lang)
            covs.append(sum(x in true_known for x in t) / len(t) if t else 0.0)
        rows.append((ndcg(rels, n_rel), float(np.mean(covs)), float(np.mean([c >= 0.9 for c in covs])), target))
        if arm == "fixed":
            continue
        toks = index_tokens(top[0]["snippet"], lang)
        unk = [t for t in toks if t not in true_known]
        share = len(unk) / len(toks) if toks else 0.0
        marked += list(dict.fromkeys(unk))[:MAXMARK]
        if arm == "adapt" or arm == "hard":
            if share > HARD:
                target = adapt_target(target, ["too_hard"], step=STEP)
            elif share < EASY and arm == "adapt":
                target = adapt_target(target, ["too_easy"], step=STEP)
    a = np.array(rows)
    return {"ndcg_all": a[:, 0].mean(), "cov_all": a[:, 1].mean(), "read_all": a[:, 2].mean(),
            "ndcg_last": a[-10:, 0].mean(), "cov_last": a[-10:, 1].mean(), "read_last": a[-10:, 2].mean(),
            "target_end": a[-1, 3]}


def run(eng=None, seeds=8):
    from .vocab import ranked_words
    eng = eng or LinguaLadder()
    qs_all = build_queries(eng)
    out, levels = {}, list(LEVELS)
    for lang, qs in qs_all.items():
        ranked = ranked_words(eng.docs[lang], lang)
        for arm in ("fixed", "marks", "hard", "adapt"):
            for true_lvl in levels:
                for decl in levels:
                    rs = [session(eng, lang, qs, true_lvl, decl, arm, ranked, s) for s in range(seeds)]
                    out[f"{lang}/{arm}/true-{true_lvl}/decl-{decl}"] = {k: round(float(np.mean([r[k] for r in rs])), 3) for k in rs[0]}
    summ = {}
    for lang in qs_all:
        for arm in ("fixed", "marks", "hard", "adapt"):
            for scope, pick in (("mismatched", lambda t, d: t != d), ("matched", lambda t, d: t == d)):
                rows = [v for k, v in out.items() if k.startswith(f"{lang}/{arm}/") and
                        pick(k.split("true-")[1].split("/")[0], k.split("decl-")[1])]
                summ[f"{lang}/{arm}/{scope}"] = {m: round(float(np.mean([r[m] for r in rows])), 3) for m in rows[0] if m != "target_end"}
    out["summary"] = summ
    (DATA_DIR / "lookup_eval.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    o = run()
    for k, v in o["summary"].items():
        print(k, v)
