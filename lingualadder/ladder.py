"""Ladder strip and "read next": the same rules as the browser version (web/app.js ladderStrip, readNext)."""

LEVELS = ("beginner", "intermediate", "advanced")


def ladder_strip(results):
    """One on-topic pick per level: the most relevant on-topic result of that level, or None.
    `results` is a wide search (k=100). Returns [] when nothing on-topic was found."""
    on = [r for r in results if r.get("on_topic")]
    if not on:
        return []
    out = []
    for lv in LEVELS:
        pick = max((r for r in on if r["level"] == lv), key=lambda r: r["relevance"], default=None)
        out.append({"level": lv, "doc": pick})
    return out


def read_next(docs, doc, read_ids=()):
    """The next article on the same topic: the nearest harder unread one, else the nearest unread one.
    Returns (doc or None, harder: bool)."""
    read = set(read_ids)
    pool = [x for x in docs if x.get("topic") == doc.get("topic") and x["id"] != doc["id"] and x["id"] not in read]
    up = sorted((x for x in pool if x["difficulty"] > doc["difficulty"]), key=lambda x: x["difficulty"])
    if up:
        return up[0], True
    if pool:
        return min(pool, key=lambda x: abs(x["difficulty"] - doc["difficulty"])), False
    return None, False
