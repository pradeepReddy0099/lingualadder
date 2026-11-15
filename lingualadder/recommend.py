"""Recommended topics: the same rule as the browser version (web/app.js renderTopics).

A topic scores the share of its articles within 0.15 of the learner's target difficulty, a small size term,
a bonus for a climbable ladder (3+ near articles plus an easier and a harder one) and a small penalty per
article already read. Topics with fewer than 3 articles are skipped. (Replaced the old raw near-count rule,
which always picked the biggest topics; see recommend_eval.py.)"""
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
    """[(topic, score, near, n, read)] best first (ties by topic name).

    score = share of the topic's articles within NEAR of the target + 0.002 * min(n, 40)
            + 0.3 if the topic has 3+ near articles plus an easier and a harder one (a climbable ladder)
            - 0.05 * articles already read."""
    read = set(read_ids)
    stat = {}
    for d in docs:
        t = d.get("topic")
        if not t:
            continue
        s = stat.setdefault(t, [0, 0, 0, 0, 0])   # n, near, read, below, above
        s[0] += 1
        diff = d["difficulty"] - target
        if abs(diff) <= NEAR:
            s[1] += 1
        elif diff < 0:
            s[3] += 1
        else:
            s[4] += 1
        if d["id"] in read:
            s[2] += 1
    out = []
    for t, (n, near, rd, below, above) in stat.items():
        if n < MIN_DOCS:
            continue
        score = near / n + 0.002 * min(n, 40) + 0.3 * (near >= 3 and below > 0 and above > 0) - 0.05 * rd
        out.append((t, score, near, n, rd))
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
