"""Offline simulation of the adaptive target: a simulated learner has a hidden ideal difficulty,
gives too_easy/too_hard feedback on the top result, and we measure how far result difficulty
is from the ideal with and without adaptation."""
import json, numpy as np
from lingualadder.search import LinguaLadder, adapt_target
from lingualadder.config import DATA_DIR
QS = {"en": ["volcano", "music", "river", "history of rome", "football", "medicine"],
      "es": ["volcán", "música", "río", "historia de roma", "fútbol", "medicina"]}
def sim(eng, lang, ideal, start, adapt, step=0.07, tol=0.1):
    t, gaps = start, []
    for r in range(3):
        for q in QS[lang]:
            res = eng.search(lang, q, t)
            if not res: continue
            gaps.append(abs(np.mean([x["difficulty"] for x in res]) - ideal))
            if adapt:
                d = res[0]["difficulty"]
                fb = "too_easy" if d < ideal - tol else "too_hard" if d > ideal + tol else None
                if fb: t = adapt_target(t, [fb], step=step, lo=0.0, hi=1.0)
    return float(np.mean(gaps)), t
if __name__ == "__main__":
    eng = LinguaLadder(); out = {}
    for lang in ("en", "es"):
        ds = np.array([d["difficulty"] for d in eng.docs[lang]])
        for name, ideal in (("low", np.quantile(ds, .2)), ("high", np.quantile(ds, .8))):
            for start in (0.2, 0.5, 0.8):
                f, tf = sim(eng, lang, ideal, start, False); a, ta = sim(eng, lang, ideal, start, True)
                out[f"{lang}/{name}/start{start}"] = {"ideal": round(float(ideal), 3), "fixed_gap": round(f, 3), "adaptive_gap": round(a, 3), "final_target": round(ta, 3)}
    gm = lambda k: round(float(np.mean([v[k] for v in out.values()])), 3)
    out["mean"] = {"fixed_gap": gm("fixed_gap"), "adaptive_gap": gm("adaptive_gap")}
    (DATA_DIR / "adapt_eval.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out["mean"]))
    for k, v in out.items(): print(k, v)

def sweep(eng=None):
    """Mean adaptive gap over the same scenarios for several step sizes and dead-zone tolerances."""
    eng = eng or LinguaLadder(); res = {}
    for step in (0.03, 0.05, 0.07, 0.1, 0.15):
        for tol in (0.05, 0.1, 0.15):
            gaps = []
            for lang in ("en", "es"):
                ds = np.array([d["difficulty"] for d in eng.docs[lang]])
                for ideal in (np.quantile(ds, .2), np.quantile(ds, .8)):
                    for start in (0.2, 0.5, 0.8):
                        gaps.append(sim(eng, lang, ideal, start, True, step=step, tol=tol)[0])
            res[f"step{step}_tol{tol}"] = round(float(np.mean(gaps)), 3)
    return res

def sim_noisy(eng, lang, ideal, start, step=0.07, decay=1.0, flip=0.2, seed=0, tol=0.1):
    """Noisy learner: with probability `flip` the feedback is wrong/random. Step shrinks by `decay` per feedback."""
    rng = np.random.default_rng(seed); t, gaps, s = start, [], step
    for r in range(3):
        for q in QS[lang]:
            res = eng.search(lang, q, t)
            if not res: continue
            gaps.append(abs(np.mean([x["difficulty"] for x in res]) - ideal))
            d = res[0]["difficulty"]
            fb = "too_easy" if d < ideal - tol else "too_hard" if d > ideal + tol else None
            if rng.random() < flip: fb = rng.choice(["too_easy", "too_hard", None])
            if fb:
                t = adapt_target(t, [fb], step=s, lo=0.0, hi=1.0); s *= decay
    return float(np.mean(gaps))

def noisy_sweep(eng=None):
    eng = eng or LinguaLadder(); res = {}
    for step in (0.07, 0.15):
        for decay in (1.0, 0.95, 0.9):
            for flip in (0.0, 0.3):
                g = []
                for lang in ("en", "es"):
                    ds = np.array([d["difficulty"] for d in eng.docs[lang]])
                    for ideal in (np.quantile(ds, .2), np.quantile(ds, .8)):
                        for start in (0.2, 0.5, 0.8):
                            for seed in range(3):
                                g.append(sim_noisy(eng, lang, ideal, start, step, decay, flip, seed))
                res[f"step{step}_decay{decay}_flip{flip}"] = round(float(np.mean(g)), 3)
    return res
