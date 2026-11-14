"""Placement test (server side): estimates a learner's reading level from performance, not self-report.

Same method as web/placement.js, for the Flask app.
Part 1 (vocabulary): yes/no checklist of real words from six corpus-frequency bands plus invented
  pseudowords; the hit rate is corrected for guessing with the false-alarm rate (Meara-style).
Part 2 (reading): adaptive cloze. Each item is the opening of a real article at a given difficulty
  quantile with one content word blanked and four options; a staircase moves the quantile up after a
  correct answer and down after a wrong one, with a shrinking step.
The two parts combine into a difficulty quantile, turned into a per-language target difficulty.
"""
import random
import re

from .textproc import STOP

VOWELS = "aeiou"
LETTERS = r"[^\W\d_]"
_WORD = re.compile(LETTERS + "+")
_SENT = re.compile(r"[^.!?]+[.!?]")


class _Pool:
    """Per-language word list (ranked by document frequency) and articles ordered by difficulty."""

    def __init__(self, engine, lang):
        idx, docs = engine.indexes[lang], engine.docs[lang]
        stop = STOP.get(lang, set())
        seen = set()
        for d in docs:
            for w in _WORD.findall(d.get("snippet", "")):
                if len(w) >= 4 and w.islower() and w not in stop:
                    seen.add(w)
        ws = [(w, len(idx.postings[w])) for w in seen if w in idx.postings and len(idx.postings[w]) >= 2]
        ws.sort(key=lambda x: (-x[1], x[0]))
        n = max(len(ws) - 1, 1)
        self.words = [(w, i / n) for i, (w, _) in enumerate(ws)]   # (word, rank in 0..1)
        self.rank = dict(self.words)
        self.postings = idx.postings
        self.docs = docs
        self.order = sorted(range(len(docs)), key=lambda i: (float(docs[i]["difficulty"]), i))
        self.sorted_diff = [float(docs[i]["difficulty"]) for i in self.order]


_POOLS = {}


def pool(engine, lang):
    key = (id(engine), lang)
    if key not in _POOLS:
        _POOLS[key] = _Pool(engine, lang)
    return _POOLS[key]


def _pseudoword(p, mid, r):
    for _ in range(200):
        base = r.choice(mid)[0]
        if len(base) < 5 or not re.fullmatch(r"[a-zñ]+", base):
            continue
        ch = list(base)
        vi = [i for i, c in enumerate(ch) if c in VOWELS and i > 0]
        if len(vi) < 2:
            continue
        i = r.choice(vi)
        ch[i] = r.choice([v for v in VOWELS if v != ch[i]])
        if r.random() < 0.5:
            j = 1 + int(r.random() * (len(ch) - 2))
            if ch[j] not in VOWELS and ch[j + 1] not in VOWELS:
                ch[j], ch[j + 1] = ch[j + 1], ch[j]
        w = "".join(ch)
        if w not in p.postings and w not in p.rank:
            return w
    return None


def vocab_items(engine, lang, seed):
    """18 real words (3 from each of 6 frequency bands) + up to 6 pseudowords, shuffled."""
    p, r = pool(engine, lang), random.Random(seed)
    ws = [x for x in p.words if len(x[0]) >= 4]
    items = []
    for b in range(6):
        band = [x for x in ws if b / 6 <= x[1] < (b + 1) / 6 + (1e-9 if b == 5 else 0)]
        r.shuffle(band)
        items += [{"word": w, "real": True, "band": b} for w, _ in band[:3]]
    mid = [x for x in ws if 0.2 < x[1] < 0.8]
    for _ in range(6):
        w = _pseudoword(p, mid, r)
        if w:
            items.append({"word": w, "real": False, "band": -1})
    r.shuffle(items)
    return items


def score_vocab(items, answers):
    """answers: list of booleans aligned with items ("I know this word"). Returns 0..1."""
    h = nr = f = npw = 0
    for it, a in zip(items, answers):
        if it["real"]:
            nr += 1
            h += bool(a)
        else:
            npw += 1
            f += bool(a)
    H = h / nr if nr else 0.0
    F = f / npw if npw else 0.0
    if F >= 1:
        return 0.0
    return max(0.0, min(1.0, (H - F) / (1 - F)))


def quantile_to_target(engine, lang, q):
    s = pool(engine, lang).sorted_diff
    return s[min(len(s) - 1, max(0, round(q * (len(s) - 1))))]


def cloze_item(engine, lang, q, r, used):
    """One cloze item from an article near difficulty quantile q; None if nothing fits."""
    p = pool(engine, lang)
    n = len(p.order)
    center = round(q * (n - 1))
    spread = 15
    while spread < n:
        cand = p.order[max(0, center - spread):min(n, center + spread)]
        cand = cand[:]
        r.shuffle(cand)
        for di in cand:
            if di in used:
                continue
            d = p.docs[di]
            text = (d.get("snippet") or "").rstrip("…").strip()
            text = " ".join(_SENT.findall(text)[:2]).strip()
            if not 70 <= len(text) <= 320:
                continue
            toks = re.findall(LETTERS + "{5,}", text)
            toks = [t for t in toks if t.islower()]
            title = d["title"].lower()
            cands = [(w, p.rank[w]) for w in toks if w in p.rank and 0.08 < p.rank[w] < 0.9 and w not in title]
            if not cands:
                continue
            ans, arank = r.choice(cands)
            pool_ = [w for w, rk in p.words if w != ans and abs(rk - arank) < 0.15 and abs(len(w) - len(ans)) <= 2 and w not in toks]
            same = [w for w in pool_ if w[-2:] == ans[-2:]]
            src = same if len(same) >= 3 else pool_
            if len(src) < 3:
                continue
            ds = r.sample(src, 3)
            pat = re.compile("(?<!" + LETTERS + ")" + re.escape(ans) + "(?!" + LETTERS + ")")
            opts = [ans] + ds
            r.shuffle(opts)
            return {"doc": di, "title": d["title"], "q": q, "text": pat.sub("_____", text, count=1),
                    "answer": ans, "options": opts}
        spread *= 2
    return None


class Staircase:
    """Adaptive staircase over difficulty quantiles; serializable for the session."""

    def __init__(self, n=8, q=0.5, step=0.25, history=None):
        self.q, self.step, self.n = q, step, n
        self.history = history or []

    def record(self, correct):
        self.history.append({"q": self.q, "correct": bool(correct)})
        self.q = min(0.97, max(0.03, self.q + (self.step if correct else -self.step)))
        self.step = max(0.06, self.step * 0.6)

    def done(self):
        return len(self.history) >= self.n

    def estimate(self):
        """Mean of the last few quantiles visited, which is where the staircase settles."""
        qs = ([h["q"] for h in self.history] + [self.q])[-4:]
        return sum(qs) / len(qs)

    def to_dict(self):
        return {"q": self.q, "step": self.step, "n": self.n, "history": self.history}

    @classmethod
    def from_dict(cls, d):
        return cls(d["n"], d["q"], d["step"], list(d["history"]))


def combine(engine, lang, vocab_score, cloze_q):
    q = min(0.97, max(0.03, 0.6 * cloze_q + 0.4 * vocab_score))
    target = quantile_to_target(engine, lang, q)
    level = "beginner" if target < 0.35 else "intermediate" if target < 0.65 else "advanced"
    return {"quantile": q, "target": target, "level": level}
