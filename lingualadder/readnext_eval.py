"""Read-next ordering per language: step size of the suggested next article.
Rules: nearest (current: nearest harder), goal (harder article closest to +GOAL, within 0.02..0.20).
Measured over every article as the start: share with a harder suggestion, median/mean step, share of steps in [0.02,0.15].
python -m lingualadder.readnext_eval -> data/readnext_eval.json"""
import json, statistics as st
from .config import DATA_DIR
from .search import LinguaLadder
GOAL = 0.08
def pools(docs):
    p = {}
    for d in docs:
        if d.get("topic"): p.setdefault(d["topic"], []).append(d)
    return p
def pick(pool, d, rule):
    up = [x for x in pool if x["id"] != d["id"] and x["difficulty"] > d["difficulty"]]
    if not up: return None
    if rule == "nearest": return min(up, key=lambda x: x["difficulty"])
    c = [x for x in up if 0.02 <= x["difficulty"] - d["difficulty"] <= 0.20]
    pool_ = c or up
    return min(pool_, key=lambda x: abs(x["difficulty"] - d["difficulty"] - GOAL))
def main():
    eng = LinguaLadder(); out = {}
    for lang in ("en", "es"):
        docs = eng.docs[lang]; P = pools(docs); res = {}
        for rule in ("nearest", "goal"):
            steps = []; n = 0
            for d in docs:
                if not d.get("topic"): continue
                n += 1; x = pick(P[d["topic"]], d, rule)
                if x: steps.append(x["difficulty"] - d["difficulty"])
            res[rule] = {"start_articles": n, "has_harder": round(len(steps)/n, 3),
                "median_step": round(st.median(steps), 4), "mean_step": round(st.mean(steps), 4),
                "share_step_0.02_0.15": round(sum(0.02 <= s <= 0.15 for s in steps)/len(steps), 3),
                "share_step_lt_0.005": round(sum(s < 0.005 for s in steps)/len(steps), 3)}
        out[lang] = res; print(lang, json.dumps(res))
    json.dump(out, open(DATA_DIR/"readnext_eval.json", "w"), indent=1)
if __name__ == "__main__": main()
