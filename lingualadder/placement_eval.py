"""Simulated-learner comparison of placement estimators (guessing-aware scoring).

Learner model: P(correct | ability a, item quantile q) = 0.25 + 0.75 * sigmoid(slope * (a - q)).
The estimators only ever assume slope 8; the true slope is varied to check robustness.
Run: python -m lingualadder.placement_eval   (writes data/placement_eval.json)
"""
import json
import math
import random
import sys

from .placement import Staircase

ABILITIES = [0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9]


def simulate(n_items, slope, n_sims, seed=0):
    out = {"mean4": [], "eap": []}
    for a in ABILITIES:
        for s in range(n_sims):
            r = random.Random(seed + s * 7919 + int(a * 1000))
            st = Staircase(n=n_items)
            while not st.done():
                p = 0.25 + 0.75 / (1 + math.exp(-(a - st.q) * slope))
                st.record(r.random() < p)
            out["mean4"].append((a, st.estimate_mean4()))
            out["eap"].append((a, st.estimate()))
    return out


def summarize(pairs):
    err = [abs(e - a) for a, e in pairs]
    bias = {a: sum(e for b, e in pairs if b == a) / sum(1 for b, _ in pairs if b == a) - a for a in ABILITIES}
    sd = {}
    for a in ABILITIES:
        es = [e for b, e in pairs if b == a]
        m = sum(es) / len(es)
        sd[a] = (sum((x - m) ** 2 for x in es) / len(es)) ** 0.5
    weak = [abs(e - a) for a, e in pairs if a <= 0.25]
    return {"mae": round(sum(err) / len(err), 3), "mae_weak": round(sum(weak) / len(weak), 3),
            "bias": {str(a): round(b, 3) for a, b in bias.items()},
            "mean_sd": round(sum(sd.values()) / len(sd), 3)}


def main(n_sims=200):
    res = {}
    for n_items in (8, 12):
        for slope in (5, 8, 12):
            sim = simulate(n_items, slope, n_sims)
            res[f"n{n_items}_slope{slope}"] = {k: summarize(v) for k, v in sim.items()}
    json.dump(res, open("data/placement_eval.json", "w"), indent=1)
    for k, v in res.items():
        print(k, "mean4 mae", v["mean4"]["mae"], "weak", v["mean4"]["mae_weak"], "| eap mae", v["eap"]["mae"], "weak", v["eap"]["mae_weak"])
    print("bias n8 slope8 mean4", res["n8_slope8"]["mean4"]["bias"])
    print("bias n8 slope8 eap  ", res["n8_slope8"]["eap"]["bias"])


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
