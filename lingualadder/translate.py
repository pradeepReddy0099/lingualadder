"""Highlight-to-translate with caching.

Primary: Google Translate (public gtx endpoint, no key, 100+ languages).
Fallback: MyMemory free API. If GOOGLE_API_KEY is set, the official Cloud
Translation v2 API is used instead.
"""
import json
import os
import sqlite3
import threading

import requests

from .config import DATA_DIR, USER_AGENT

_DB = DATA_DIR / "translation_cache.sqlite"
_lock = threading.Lock()
_conn = sqlite3.connect(_DB, check_same_thread=False)
_conn.execute("CREATE TABLE IF NOT EXISTS cache (src TEXT, tgt TEXT, q TEXT, out TEXT, PRIMARY KEY (src, tgt, q))")


def _google_official(q, src, tgt, key):
    r = requests.post("https://translation.googleapis.com/language/translate/v2",
                      params={"key": key}, data={"q": q, "source": src, "target": tgt, "format": "text"},
                      timeout=10)
    r.raise_for_status()
    return r.json()["data"]["translations"][0]["translatedText"]


def _google_gtx(q, src, tgt):
    r = requests.get("https://translate.googleapis.com/translate_a/single",
                     params={"client": "gtx", "sl": src, "tl": tgt, "dt": "t", "q": q},
                     headers={"User-Agent": USER_AGENT}, timeout=10)
    r.raise_for_status()
    return "".join(part[0] for part in r.json()[0] if part and part[0])


def _mymemory(q, src, tgt):
    r = requests.get("https://api.mymemory.translated.net/get",
                     params={"q": q, "langpair": f"{src}|{tgt}"}, timeout=10)
    r.raise_for_status()
    return r.json()["responseData"]["translatedText"]


def translate(q: str, src: str, tgt: str) -> dict:
    q = " ".join(q.split())[:500]
    if not q or src == tgt:
        return {"text": q, "engine": "none", "cached": False}
    with _lock:
        row = _conn.execute("SELECT out FROM cache WHERE src=? AND tgt=? AND q=?", (src, tgt, q)).fetchone()
    if row:
        return {"text": row[0], "engine": "cache", "cached": True}
    key = os.environ.get("GOOGLE_API_KEY")
    engines = ([("google-cloud", lambda: _google_official(q, src, tgt, key))] if key else []) + [
        ("google", lambda: _google_gtx(q, src, tgt)),
        ("mymemory", lambda: _mymemory(q, src, tgt)),
    ]
    for name, fn in engines:
        try:
            out = fn()
            if out:
                with _lock:
                    _conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)", (src, tgt, q, out))
                    _conn.commit()
                return {"text": out, "engine": name, "cached": False}
        except Exception:
            continue
    return {"text": None, "engine": None, "cached": False, "error": "translation unavailable"}
