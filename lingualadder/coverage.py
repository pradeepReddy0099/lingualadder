"""Level coverage: every topic should have at least one beginner, intermediate and advanced article.

python -m lingualadder.coverage            report gaps (writes data/coverage.json)
python -m lingualadder.coverage --fill     fetch candidates for every gap into data/raw/fill_<lang>.jsonl,
                                           rebuild, re-check; repeats up to --rounds times

Difficulty scores are z-scored within each language, so a new article's level is only known after a
rebuild; that is why filling works in rounds. Candidates per gap:
  beginner      easy-source search (Simple English Wikipedia / Vikidia) for the topic
  intermediate  easy-source search plus short regular articles (fewer than ~700 words) from Wikipedia search
  advanced      regular Wikipedia search
"""
import argparse, json, subprocess, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from .config import DATA_DIR, EASY_SOURCES, RAW_DIR, wiki_api

LEVELS = ("beginner", "intermediate", "advanced")


def report(write=True):
    import pickle
    blob = pickle.load(open(DATA_DIR / "index.pkl", "rb"))
    out = {}
    for lang, docs in blob["docs"].items():
        cov, label = defaultdict(lambda: defaultdict(int)), {}
        for d in docs:
            if d.get("topic"):
                cov[d["topic"]][d["level"]] += 1
                if d.get("en_title") == d["topic"] and not d.get("easy"):
                    label[d["topic"]] = d["title"]
        topics = {t: {lv: c.get(lv, 0) for lv in LEVELS} for t, c in cov.items()}
        gaps = {t: [lv for lv in LEVELS if not c[lv]] for t, c in topics.items() if any(not c[lv] for lv in LEVELS)}
        out[lang] = {"topics": len(topics), "complete": len(topics) - len(gaps), "gaps": gaps,
                     "labels": {t: label.get(t, t) for t in gaps}}
        print(f"{lang}: {len(topics) - len(gaps)}/{len(topics)} topics have all three levels")
    if write:
        json.dump(out, open(DATA_DIR / "coverage.json", "w"), ensure_ascii=False, indent=1)
    return out


def search(url, q, n):
    from .collect import api
    data = api(url, action="query", list="search", srsearch=q, srlimit=n, srnamespace=0)
    return [r["title"] for r in data.get("query", {}).get("search", [])]


def fill_round(cov, per_gap=8, workers=24):
    from .collect import fetch_extract
    existing = set()
    for p in RAW_DIR.glob("*.jsonl"):
        for line in open(p, encoding="utf-8"):
            d = json.loads(line); existing.add((d["source"], d["title"]))
    added = 0
    for lang, info in cov.items():
        easy_url, reg_url = EASY_SOURCES[lang], wiki_api(lang)
        easy_src = "simple.wikipedia" if lang == "en" else f"{lang}.vikidia"
        def plan(item):
            topic, missing = item
            q = info["labels"].get(topic, topic)
            out = []
            if "beginner" in missing or "intermediate" in missing:
                out += [(easy_url, t, {"lang": lang, "source": easy_src, "topic": topic, "en_title": None, "easy": 1, "_fill": "easy"})
                        for t in search(easy_url, q, per_gap)]
            if missing:   # beginner/intermediate gaps also look at short regular articles (stubs are often easy)
                out += [(reg_url, t, {"lang": lang, "source": f"{lang}.wikipedia", "topic": topic, "en_title": None, "easy": 0,
                                      "_fill": "short" if "advanced" not in missing else "any"})
                        for t in search(reg_url, q, per_gap * 2)]
            return out
        with ThreadPoolExecutor(workers) as ex:
            jobs = [j for js in ex.map(plan, info["gaps"].items()) for j in js]
        print(f"  {lang}: {len(jobs)} search candidates", flush=True)
        jobs = [j for j in jobs if (j[2]["source"], j[1]) not in existing]

        def get(job):
            url, title, meta = job
            a = fetch_extract(url, title)
            if not a:
                return None
            if meta["_fill"] == "short" and len(a["text"].split()) > 700:
                return None
            a.update({k: v for k, v in meta.items() if k != "_fill"})
            return a
        arts, done = [], 0
        with ThreadPoolExecutor(workers) as ex, open(RAW_DIR / f"fill_{lang}.jsonl", "a", encoding="utf-8") as f:
            for a in ex.map(get, jobs):
                done += 1
                if a:
                    arts.append(a); f.write(json.dumps(a, ensure_ascii=False) + "\n"); f.flush()
                if done % 200 == 0: print(f"    {lang}: {done}/{len(jobs)} fetched, {len(arts)} kept", flush=True)
        print(f"  {lang}: +{len(arts)} candidate articles for {len(info['gaps'])} topics with gaps")
        added += len(arts)
    return added


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fill", action="store_true")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--per-gap", type=int, default=0, help="search results per gap (default grows 4, 8, 12 per round)")
    a = ap.parse_args()
    cov = report()
    if not a.fill:
        return
    for r in range(a.rounds):
        if not any(v["gaps"] for v in cov.values()):
            break
        print(f"Round {r + 1}: filling gaps ...")
        if not fill_round(cov, per_gap=a.per_gap or 4 * (r + 1)):
            break
        subprocess.run([sys.executable, "-m", "lingualadder.build"], check=True)
        cov = report()


if __name__ == "__main__":
    main()
