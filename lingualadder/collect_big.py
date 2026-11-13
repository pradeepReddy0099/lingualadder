"""Resumable large collection for English and Spanish (target ~5,000 articles per language).

Stages are cached in data/raw_big/ so the script can be re-run until it finishes:
  1. titles.json  - topical English titles from `morelike:` over many seed topics
  2. links.json   - interlanguage links (es, simple)
  3. <source>.jsonl - article text, appended; already-fetched titles are skipped
At the end, `--finalize` writes capped files into data/raw/.

Usage: python -m lingualadder.collect_big [--per-seed 40] [--target 5000] [--finalize]
"""
import argparse, json, random, time
from concurrent.futures import ThreadPoolExecutor
from .config import RAW_DIR, SEED_TOPICS, EASY_SOURCES, wiki_api
from .collect import similar_titles, langlinks, fetch_extract, random_titles, existing_titles

BIG = RAW_DIR.parent / "raw_big"
EXTRA_SEEDS = [
 "Lion","Horse","Dog","Cat","Whale","Penguin","Snake","Frog","Ant","Spider","Eagle","Wolf","Bear","Dolphin","Octopus",
 "Tree","Flower","Mushroom","Desert","River","Lake","Mountain","Glacier","Island","Weather","Hurricane","Tornado","Volcanic eruption",
 "Sun","Mars","Jupiter","Star","Galaxy","Black hole","Comet","Telescope","Gravity","Electricity","Magnetism","Light","Sound","Atom",
 "Water","Fire","Iron","Gold","Plastic","Glass","Oil","Recycling","Renewable energy","Nuclear power","Solar energy","Wind power",
 "Human body","Heart","Blood","Bone","Sleep","Nutrition","Fruit","Vegetable","Cheese","Pasta","Sugar","Salt","Corn","Potato","Apple",
 "Banana","Orange (fruit)","Ice cream","Soup","Sushi","Taco","Wine","Beer","Milk","Egg as food",
 "Smartphone","Television","Radio","Robot","Video game","Social media","Electric car","Car","Ship","Rocket","Bridge","Skyscraper",
 "Printing press","Wheel","Clock","Camera","Electric light","Telephone","Satellite",
 "Spain","Mexico","Argentina","Colombia","Peru","Chile","Cuba","United States","Canada","Brazil","France","Italy","Germany",
 "United Kingdom","China","Japan","India","Egypt","Australia","Russia","Madrid","Barcelona","Mexico City","Buenos Aires","New York City",
 "London","Paris","Rome","Amazon River","Andes","Sahara","Antarctica","Pacific Ocean","Mediterranean Sea",
 "Christopher Columbus","Miguel de Cervantes","Pablo Picasso","Salvador Dalí","Gabriel García Márquez","Simón Bolívar","Napoleon",
 "William Shakespeare","Isaac Newton","Charles Darwin","Marie Curie","Nelson Mandela","Martin Luther King Jr.","Abraham Lincoln",
 "Cleopatra","Julius Caesar","Aztecs","Maya civilization","Inca Empire","Middle Ages","Renaissance","Industrial Revolution",
 "World War I","World War II","Cold War","French Revolution","American Revolution","Spanish Civil War",
 "Democracy","Election","Money","Bank","Trade","Tourism","School","University","Language","Writing","Library","Book","Newspaper",
 "Poetry","Novel","Theatre","Opera","Dance","Flamenco","Tango","Jazz","Rock music","Hip hop music","Piano","Violin","Drum",
 "Cinema of Spain","Animation","Photography","Sculpture","Architecture","Museum","Christmas","Easter","Day of the Dead","Carnival",
 "Religion","Mythology","Greek mythology","Philosophy","Mathematics","Geometry","Number","Physics","Chemistry","Biology","Medicine",
 "Hospital","Disease","Bacteria","Virus","Evolution","DNA","Cell (biology)","Ecology","Pollution","Forest","Agriculture","Farm",
 "Baseball","Swimming","Running","Boxing","Cycling","Golf","Rugby football","Volleyball","Skiing","FIFA World Cup","Real Madrid CF",
 "FC Barcelona","Formula One","Marathon","Martial arts","Family","Friendship","Emotion","Happiness","Holiday","Camping","Fashion",
 "Clothing","Shoe","House","City","Village","Police","Firefighter","Doctor","Teacher","Engineer","Law","Human rights","Climate",
]

def jload(p, default):
    return json.load(open(p)) if p.exists() else default

def fetch_append(name, url, items, workers, deadline):
    path = BIG / f"{name}.jsonl"
    done = set()
    if path.exists():
        for line in open(path, encoding="utf-8"):
            try: done.add(json.loads(line)["_req"])
            except Exception: pass
    todo = [it for it in items if it[0] not in done]
    print(f"  {name}: {len(done)} done, {len(todo)} to fetch", flush=True)
    def job(it):
        if time.time() > deadline: return it[0], "SKIP"
        art = fetch_extract(url, it[0])
        if art: art.update(it[1]); art["_req"] = it[0]
        return it[0], art
    with open(path, "a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as ex:
        for req, art in ex.map(job, todo):
            if art == "SKIP": continue
            f.write(json.dumps(art if art else {"_req": req, "_missing": 1}, ensure_ascii=False) + "\n")
    return time.time() <= deadline

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-seed", type=int, default=40)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--target", type=int, default=5000)
    ap.add_argument("--budget", type=int, default=1000, help="seconds before stopping cleanly")
    ap.add_argument("--finalize", action="store_true")
    a = ap.parse_args()
    BIG.mkdir(exist_ok=True)
    deadline = time.time() + a.budget
    seeds = list(dict.fromkeys(SEED_TOPICS + EXTRA_SEEDS))
    tp = BIG / "titles.json"; topic_of = jload(tp, {})
    done_seeds = set(topic_of.get("__seeds__", []))
    for s in seeds:
        if s in done_seeds: continue
        if time.time() > deadline: json.dump(topic_of, open(tp, "w")); print("stopped in stage 1"); return
        for t in similar_titles(s, a.per_seed): topic_of.setdefault(t, s)
        done_seeds.add(s); topic_of["__seeds__"] = sorted(done_seeds)
    json.dump(topic_of, open(tp, "w"))
    titles = [t for t in topic_of if t != "__seeds__"]
    print(f"{len(titles)} English titles over {len(seeds)} seeds", flush=True)
    lp = BIG / "links.json"; links = jload(lp, None)
    if links is None:
        links = langlinks(titles, {"es", "simple"}); json.dump(links, open(lp, "w"))
    random.seed(0)
    order = titles[:]; random.shuffle(order)
    meta = lambda t, lang, src, easy: {"lang": lang, "source": src, "topic": topic_of[t], "en_title": t, "easy": easy}
    ok = fetch_append("enwiki", wiki_api("en"), [(t, meta(t, "en", "en.wikipedia", 0)) for t in order[: int(a.target * 1.1)]], a.workers, deadline)
    es_items = [(links[t]["es"], meta(t, "es", "es.wikipedia", 0)) for t in order if links.get(t, {}).get("es")]
    ok = ok and fetch_append("eswiki", wiki_api("es"), es_items[: int(a.target * 1.1)], a.workers, deadline)
    ok = ok and fetch_append("simplewiki", EASY_SOURCES["en"], [(links[t]["simple"], meta(t, "en", "simple.wikipedia", 1)) for t in order if links.get(t, {}).get("simple")][:1500], a.workers, deadline)
    vp = BIG / "vikidia_titles.json"; vik = jload(vp, None)
    if ok and vik is None:
        cand = {links[t]["es"]: t for t in order if links.get(t, {}).get("es")}
        found = existing_titles(EASY_SOURCES["es"], list(cand))
        vik = [[vt, cand[o]] for o, vt in found.items()]; json.dump(vik, open(vp, "w"))
    if ok:
        ok = fetch_append("esvikidia", EASY_SOURCES["es"], [(vt, meta(o, "es", "es.vikidia", 1)) for vt, o in vik][:1500], a.workers, deadline)
    print("ALL STAGES DONE" if ok else "stopped on time budget; re-run to continue", flush=True)
    if a.finalize: finalize(a.target)

def read(name):
    p = BIG / f"{name}.jsonl"
    out, seen = [], set()
    if not p.exists(): return out
    for line in open(p, encoding="utf-8"):
        d = json.loads(line)
        if d.get("_missing") or d["pageid"] in seen: continue
        seen.add(d["pageid"]); d.pop("_req", None); out.append(d)
    return out

MAX_PART = 20 * 1024 * 1024   # GitHub web upload allows 25 MB per file; keep parts under 20 MB

def write_parts(name, arts):
    """Write articles to data/raw/<name>.jsonl, or <name>_p1.jsonl, _p2.jsonl ... when bigger than MAX_PART."""
    for old in list(RAW_DIR.glob(f"{name}.jsonl")) + list(RAW_DIR.glob(f"{name}_p*.jsonl")): old.unlink()
    parts, cur, size = [], [], 0
    for x in arts:
        line = json.dumps(x, ensure_ascii=False) + "\n"
        b = len(line.encode("utf-8"))
        if cur and size + b > MAX_PART: parts.append(cur); cur, size = [], 0
        cur.append(line); size += b
    if cur: parts.append(cur)
    for k, lines in enumerate(parts, 1):
        fn = f"{name}.jsonl" if len(parts) == 1 else f"{name}_p{k}.jsonl"
        with open(RAW_DIR / fn, "w", encoding="utf-8") as f: f.writelines(lines)
    return len(parts)

def finalize(target=None):
    """Write data/raw files with NO article cap: every fetched article is kept (plus any older curated ones),
    split into parts under 20 MB. `target` is ignored (kept for command-line compatibility)."""
    def load_old(n):
        out = []
        for p in sorted(RAW_DIR.glob(f"{n}.jsonl")) + sorted(RAW_DIR.glob(f"{n}_p*.jsonl")):
            out += [json.loads(l) for l in open(p, encoding="utf-8")]
        return out
    for lang, reg, easy, rnd in (("en", "enwiki", "simplewiki", "enwiki_random"), ("es", "eswiki", "esvikidia", "eswiki_random")):
        res = {}
        for name in (reg, easy):
            arts, seen = read(name), set()
            arts_ids = {x["pageid"] for x in arts}
            old = [x for x in load_old(name) if x["pageid"] not in arts_ids]   # keep older curated articles too
            arts = arts + old
            res[name] = (arts, write_parts(name, arts))
        r = load_old(rnd)
        print(f"{lang}: {len(res[reg][0])} regular ({res[reg][1]} files) + {len(res[easy][0])} easy ({res[easy][1]} files) + {len(r)} random")

if __name__ == "__main__":
    main()
