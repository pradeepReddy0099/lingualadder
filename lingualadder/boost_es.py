"""Grow the Spanish corpus to parity with English (user request 2026-11-12: Spanish and English equally important).

python -m lingualadder.boost_es [--easy-target N] [--total-target N]

For each seed topic, searches Vikidia (easy Spanish) and Spanish Wikipedia with the topic's Spanish label
and appends new, de-duplicated articles to data/raw_big/es_boost.jsonl (resumable). Defaults: reach the
English counts for easy (Simple English) and total articles. Merge into data/raw/ afterwards
(python -m lingualadder.boost_es --merge), then rebuild and run the coverage check.
"""
import argparse, glob, json, pickle, shutil
from concurrent.futures import ThreadPoolExecutor

from .config import DATA_DIR, EASY_SOURCES, RAW_DIR, wiki_api
from .coverage import search

OUT = DATA_DIR / "raw_big" / "es_boost.jsonl"


def counts():
    seen, c = set(), {}
    for p in sorted(glob.glob(str(RAW_DIR / "*.jsonl"))) + ([str(OUT)] if OUT.exists() else []):
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            if d["lang"] not in ("en", "es"):
                continue
            seen.add((d["source"], d["title"]))
            c[d["source"]] = c.get(d["source"], 0) + 1
    return seen, c


def main():
    from .collect import fetch_extract
    ap = argparse.ArgumentParser()
    ap.add_argument("--easy-target", type=int)
    ap.add_argument("--total-target", type=int)
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    if a.merge:
        shutil.copy(OUT, RAW_DIR / "es_boost.jsonl"); print("merged", OUT, "->", RAW_DIR / "es_boost.jsonl"); return
    seen, c = counts()
    en_easy, en_tot = c.get("simple.wikipedia", 0), c.get("simple.wikipedia", 0) + c.get("en.wikipedia", 0)
    easy_t = a.easy_target or en_easy
    tot_t = a.total_target or en_tot
    es_easy = c.get("es.vikidia", 0); es_reg = c.get("es.wikipedia", 0)
    print(f"en easy {en_easy}, en total {en_tot}; es easy {es_easy}, es total {es_easy + es_reg}; targets easy {easy_t}, total {tot_t}")
    blob = pickle.load(open(DATA_DIR / "index.pkl", "rb"))
    labels = {}
    for d in blob["docs"]["es"]:
        if d.get("topic") and d.get("en_title") == d["topic"] and not d.get("easy"):
            labels[d["topic"]] = d["title"]
    topics = sorted({d["topic"] for d in blob["docs"]["es"] if d.get("topic")})
    easy_url, reg_url = EASY_SOURCES["es"], wiki_api("es")
    for depth in (20, 50):
        need_easy = easy_t - es_easy
        need_reg = max(0, tot_t - (es_easy + es_reg) - max(need_easy, 0))
        if need_easy <= 0 and need_reg <= 0:
            break
        jobs = []
        for t in topics:
            q = labels.get(t, t)
            if need_easy > 0:
                jobs += [(easy_url, x, "es.vikidia", 1, t) for x in search(easy_url, q, depth)]
            if need_reg > 0:
                jobs += [(reg_url, x, "es.wikipedia", 0, t) for x in search(reg_url, q, depth // 2)]
        jobs = [j for j in dict(((j[2], j[1]), j) for j in jobs).values() if (j[2], j[1]) not in seen]

        def get(j):
            url, title, src, easy, topic = j
            art = fetch_extract(url, title)
            if not art or len(art["text"].split()) < 40:
                return None
            art.update({"lang": "es", "source": src, "easy": easy, "topic": topic, "en_title": None})
            return art
        with ThreadPoolExecutor(16) as ex, open(OUT, "a", encoding="utf-8") as f:
            for art in ex.map(get, jobs):
                if not art:
                    continue
                if art["easy"] and es_easy >= easy_t:
                    continue
                if not art["easy"] and need_reg <= 0:
                    continue
                f.write(json.dumps(art, ensure_ascii=False) + "\n"); seen.add((art["source"], art["title"]))
                if art["easy"]:
                    es_easy += 1
                else:
                    es_reg += 1; need_reg -= 1
        print(f"depth {depth}: es easy {es_easy}, es total {es_easy + es_reg}")
    print("BOOST DONE")


if __name__ == "__main__":
    main()
