"""Recommended topics, per language: do the 14 chips fit the learner's level?

For 9 learner targets (corpus difficulty quantiles 0.1 ... 0.9) the top-14 topics are scored on
  usable   share of chips with >= 3 articles within 0.15 of the target (enough to read at that level)
  ladder   share of chips with at least one article within 0.15 of the target AND one clearly easier and one clearly harder
  share    mean share of a chip's articles that are within 0.15 of the target
  near     mean number of articles within 0.15 of the target per chip
  size     median article count of the chips (large values mean big topics always win)
  covered  distinct topics shown over the 9 targets (of all topics with >= 3 articles)
Rules compared: current (near + 0.05 n), capped (min(near, CAP) + 0.05 n), ladder (capped + bonus for a climbable topic),
share (near / n), share_ladder (share + bonus for a topic with 3+ near articles and easier and harder ones).
python -m lingualadder.recommend_eval   -> data/recommend_eval.json
"""
import json
import statistics as st

from .config import DATA_DIR
from .recommend import MIN_DOCS, NEAR
from .search import LinguaLadder

QUANTILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def topic_stats(docs, target):
    s = {}
    for d in docs:
        t = d.get("topic")
        if not t:
            continue
        x = s.setdefault(t, {"n": 0, "near": 0, "below": 0, "above": 0})
        x["n"] += 1
        diff = d["difficulty"] - target
        if abs(diff) <= NEAR:
            x["near"] += 1
        elif diff < 0:
            x["below"] += 1
        else:
            x["above"] += 1
    return {t: x for t, x in s.items() if x["n"] >= MIN_DOCS}


RULES = {
    "current": lambda x: x["near"] + 0.05 * x["n"],
    "capped6": lambda x: min(x["near"], 6) + 0.05 * x["n"],
    "capped4": lambda x: min(x["near"], 4) + 0.05 * x["n"],
    "ladder": lambda x: min(x["near"], 6) + 0.05 * x["n"] + 2.0 * (x["near"] > 0 and x["below"] > 0 and x["above"] > 0),
    "share": lambda x: x["near"] / x["n"] + 0.002 * min(x["n"], 40),
    "share_ladder": lambda x: x["near"] / x["n"] + 0.002 * min(x["n"], 40) + 0.3 * (x["near"] >= 3 and x["below"] > 0 and x["above"] > 0),
}


def evaluate(docs, rule, n=14):
    diffs = sorted(d["difficulty"] for d in docs)
    usable, ladder, near, size, shown, share = [], [], [], [], set(), []
    prev = None
    churn = []
    for q in QUANTILES:
        target = diffs[round(q * (len(diffs) - 1))]
        stats = topic_stats(docs, target)
        top = sorted(stats, key=lambda t: (-RULES[rule](stats[t]), t))[:n]
        shown.update(top)
        usable += [stats[t]["near"] >= 3 for t in top]
        ladder += [stats[t]["near"] > 0 and stats[t]["below"] > 0 and stats[t]["above"] > 0 for t in top]
        near += [stats[t]["near"] for t in top]
        size += [stats[t]["n"] for t in top]
        share += [stats[t]["near"] / stats[t]["n"] for t in top]
        if prev is not None:
            churn.append(1 - len(set(top) & prev) / n)
        prev = set(top)
    allt = len(topic_stats(docs, 0.5))
    return {"usable": round(sum(usable) / len(usable), 3), "ladder": round(sum(ladder) / len(ladder), 3),
            "near": round(sum(near) / len(near), 2), "share": round(sum(share) / len(share), 3), "size": st.median(size), "covered": len(shown),
            "topics": allt, "churn": round(sum(churn) / len(churn), 3)}


def main():
    ll = LinguaLadder()
    out = {}
    for lang in ("en", "es"):
        out[lang] = {r: evaluate(ll.docs[lang], r) for r in RULES}
        for r, v in out[lang].items():
            print(lang, r, v, flush=True)
    (DATA_DIR / "recommend_eval.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
