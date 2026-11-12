"""Collect a topical, multilingual Wikipedia corpus through the MediaWiki API.

Steps
1. For each seed topic, find similar English articles with CirrusSearch
   (`morelike:`), so every article remembers which topic cluster it came from.
2. Map those English titles to the other languages with interlanguage links
   (including Simple English, the "easy" English edition).
3. Download plain text (TextExtracts) for every title in every language.
4. Add easy articles from Vikidia (Spanish and French), matched by title and
   topped up with random pages.

Output: data/raw/<source>.jsonl  (one article per line)

Usage:  python -m lingualadder.collect [--per-seed 12] [--workers 8]
"""
import argparse
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from .config import (EASY_SOURCES, LANGUAGES, RAW_DIR, SEED_TOPICS, USER_AGENT,
                     wiki_api)

S = requests.Session()
S.headers["User-Agent"] = USER_AGENT

STOP_SECTIONS = re.compile(
    r"^==+\s*(References|See also|External links|Notes|Further reading|Bibliography|Sources|"
    r"Referencias|Véase también|Enlaces externos|Notas|Bibliografía|"
    r"Références|Notes et références|Voir aussi|Liens externes|Bibliographie|"
    r"संदर्भ|सन्दर्भ|बाहरी कड़ियाँ|इन्हें भी देखें|"
    r"脚注|参考文献|関連項目|外部リンク)\s*==+\s*$", re.M)


def api(url, **params):
    params.update(format="json", formatversion=2)
    for attempt in range(4):
        try:
            r = S.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(2 + attempt * 3)
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            time.sleep(1 + attempt * 2)
    return {}


def clean_text(text: str) -> str:
    m = STOP_SECTIONS.search(text)
    if m:
        text = text[: m.start()]
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:20000]


def similar_titles(seed: str, n: int):
    data = api(wiki_api("en"), action="query", list="search",
               srsearch=f"morelike:{seed}", srlimit=n, srnamespace=0)
    return [seed] + [h["title"] for h in data.get("query", {}).get("search", [])]


def langlinks(titles, langs):
    """Map English titles -> {lang: title} via interlanguage links (50 per call)."""
    out = {t: {} for t in titles}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        cont = {}
        while True:
            data = api(wiki_api("en"), action="query", prop="langlinks", titles="|".join(batch),
                       lllimit="max", redirects=1, **cont)
            q = data.get("query", {})
            norm = {d["to"]: d["from"] for d in q.get("normalized", []) + q.get("redirects", [])}
            for page in q.get("pages", []):
                src = page["title"]
                while src in norm:
                    src = norm[src]
                if src not in out:
                    continue
                for ll in page.get("langlinks", []):
                    if ll["lang"] in langs:
                        out[src][ll["lang"]] = ll["title"]
            if "continue" in data:
                cont = data["continue"]
            else:
                break
    return out


def fetch_extract(url, title):
    data = api(url, action="query", prop="extracts|info", explaintext=1, titles=title,
               redirects=1, inprop="url")
    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        return None
    p = pages[0]
    text = clean_text(p.get("extract", "") or "")
    if len(text) < 300:
        return None
    return {"pageid": p["pageid"], "title": p["title"], "url": p.get("fullurl", ""), "text": text}


def fetch_many(url, items, workers):
    """items: list of (title, meta) -> list of article dicts with meta merged."""
    def job(item):
        title, meta = item
        art = fetch_extract(url, title)
        if art:
            art.update(meta)
        return art
    with ThreadPoolExecutor(workers) as ex:
        return [a for a in ex.map(job, items) if a]


def random_titles(url, n):
    titles = []
    while len(titles) < n:
        data = api(url, action="query", list="random", rnnamespace=0, rnlimit=min(50, n - len(titles)))
        got = [r["title"] for r in data.get("query", {}).get("random", [])]
        if not got:
            break
        titles += got
    return titles


def existing_titles(url, titles):
    found = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        data = api(url, action="query", titles="|".join(batch), redirects=1)
        q = data.get("query", {})
        norm = {d["from"]: d["to"] for d in q.get("normalized", []) + q.get("redirects", [])}
        ok = {p["title"] for p in q.get("pages", []) if "missing" not in p and "invalid" not in p}
        for t in batch:
            tt = norm.get(t, t)
            tt = norm.get(tt, tt)
            if tt in ok:
                found[t] = tt
    return found


def save(name, arts):
    path = RAW_DIR / f"{name}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for a in arts:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    print(f"  saved {len(arts):4d} articles -> {path.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-seed", type=int, default=12)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--random-easy", type=int, default=150)
    args = ap.parse_args()

    print("1) Finding topical English articles ...")
    topic_of = {}
    for seed in SEED_TOPICS:
        for t in similar_titles(seed, args.per_seed):
            topic_of.setdefault(t, seed)
    titles = list(topic_of)
    print(f"   {len(titles)} English titles across {len(SEED_TOPICS)} topics")

    print("2) Mapping to other languages ...")
    langs = set(LANGUAGES) - {"en"} | {"simple"}
    links = langlinks(titles, langs)

    print("3) Downloading article text ...")
    for lang in LANGUAGES:
        items = []
        for t in titles:
            lt = t if lang == "en" else links.get(t, {}).get(lang)
            if lt:
                items.append((lt, {"lang": lang, "source": f"{lang}.wikipedia", "topic": topic_of[t],
                                   "en_title": t, "easy": 0}))
        arts = fetch_many(wiki_api(lang), items, args.workers)
        save(f"{lang}wiki", arts)

    print("4) Downloading easy-language articles ...")
    simple_items = [(links[t]["simple"], {"lang": "en", "source": "simple.wikipedia", "topic": topic_of[t],
                                          "en_title": t, "easy": 1})
                    for t in titles if "simple" in links.get(t, {})]
    save("simplewiki", fetch_many(EASY_SOURCES["en"], simple_items, args.workers))

    for lang in ("es", "fr"):
        url = EASY_SOURCES[lang]
        cand = {links[t][lang]: t for t in titles if lang in links.get(t, {})}
        found = existing_titles(url, list(cand))
        items = [(vt, {"lang": lang, "source": f"{lang}.vikidia", "topic": topic_of[cand[orig]],
                       "en_title": cand[orig], "easy": 1}) for orig, vt in found.items()]
        seen = {vt for vt, _ in items}
        for rt in random_titles(url, args.random_easy):
            if rt not in seen:
                items.append((rt, {"lang": lang, "source": f"{lang}.vikidia", "topic": None,
                                   "en_title": None, "easy": 1}))
                seen.add(rt)
        save(f"{lang}vikidia", fetch_many(url, items, args.workers))

    # A few random regular articles per labeled language so the classifier
    # does not only see topical pages.
    print("5) Adding random regular articles for balance ...")
    for lang in ("en", "es", "fr"):
        items = [(t, {"lang": lang, "source": f"{lang}.wikipedia", "topic": None, "en_title": None, "easy": 0})
                 for t in random_titles(wiki_api(lang), args.random_easy)]
        save(f"{lang}wiki_random", fetch_many(wiki_api(lang), items, args.workers))
    print("Done.")


if __name__ == "__main__":
    random.seed(0)
    main()
