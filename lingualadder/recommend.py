"""Recommended topics: the same rule as the browser version (web/app.js renderTopics).

A topic scores (articles within 0.15 of the learner's target difficulty) + 0.05 * (all its articles)
- 0.5 * (articles already read). Topics with fewer than 3 articles are skipped."""
import json

from .config import DATA_DIR

NEAR = 0.15
MIN_DOCS = 3


def topic_labels(docs, lang):
    """Display label per seed topic: the seed article's own title, else data/topic_labels_<lang>.json."""
    labels = {d["topic"]: d["title"] for d in docs if d.get("topic") and d.get("en_title") == d["topic"] and not d.get("easy")}
    f = DATA_DIR / f"topic_labels_{lang}.json"
    if f.exists():
        for t, v in json.loads(f.read_text(encoding="utf-8")).items():
            labels.setdefault(t, v)
    return labels


def rank_topics(docs, target, read_ids=()):
    """[(topic, score, near, n, read)] best first (ties by topic name)."""
    read = set(read_ids)
    stat = {}
    for d in docs:
        t = d.get("topic")
        if not t:
            continue
        s = stat.setdefault(t, [0, 0, 0])
        s[0] += 1
        if abs(d["difficulty"] - target) <= NEAR:
            s[1] += 1
        if d["id"] in read:
            s[2] += 1
    out = [(t, s[1] + 0.05 * s[0] - 0.5 * s[2], s[1], s[0], s[2]) for t, s in stat.items() if s[0] >= MIN_DOCS]
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def recommended(docs, lang, target, read_ids=(), n=14):
    """Up to n chips: [{'topic', 'label', 'near', 'read'}] plus the total number of topics."""
    labels = topic_labels(docs, lang)
    ranked = rank_topics(docs, target, read_ids)
    chips = [{"topic": t, "label": labels.get(t, t), "near": near, "read": rd} for t, _, near, _, rd in ranked[:n]]
    if n is None:  # the full list is shown alphabetically, like the browser version
        chips.sort(key=lambda c: c["label"].lower())
    return chips, len(ranked)
