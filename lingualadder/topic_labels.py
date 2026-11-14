"""Spanish display labels for every seed topic, from English Wikipedia's language links
(en title -> es title). Writes data/topic_labels_es.json; export_web uses it when a topic has no
Spanish seed article of its own. Usage: python -m lingualadder.topic_labels"""
import json, re, urllib.parse, urllib.request
from lingualadder.config import DATA_DIR
OUT = DATA_DIR / "topic_labels_es.json"


def topics():
    seen = set()
    for f in (DATA_DIR / "raw").glob("*.jsonl"):
        if f.name[:2] in ("fr", "hi", "ja"):
            continue
        for line in f.open(encoding="utf-8"):
            try:
                t = json.loads(line).get("topic")
            except Exception:
                continue
            if t:
                seen.add(t)
    return sorted(seen)


def fetch(titles):
    q = urllib.parse.urlencode({"action": "query", "prop": "langlinks", "lllang": "es", "titles": "|".join(titles),
                                "format": "json", "redirects": 1, "lllimit": "max"})
    req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q, headers={"User-Agent": "LinguaLadder/1.0 (course project)"})
    d = json.load(urllib.request.urlopen(req, timeout=30))["query"]
    back = {}
    for r in d.get("redirects", []) + d.get("normalized", []):
        back[r["to"]] = r["from"]
    out = {}
    for p in d["pages"].values():
        for l in p.get("langlinks", []):
            out[back.get(p["title"], p["title"])] = l["*"]
    return out


def main():
    ts = topics()
    labels = {}
    for i in range(0, len(ts), 40):
        labels.update(fetch(ts[i:i + 40]))
    # drop a trailing disambiguation like "Naranja (fruta)" so the label also works as a search query
    labels = {k: re.sub(r"\s*\([^)]*\)$", "", v) for k, v in labels.items() if k in ts}
    OUT.write_text(json.dumps(labels, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(len(ts), "topics,", len(labels), "Spanish labels; missing:", [t for t in ts if t not in labels])


if __name__ == "__main__":
    main()
