"""Language-aware text processing that works for any script.

* Words are runs of letters and combining marks (\\p{L}\\p{M}), so Devanagari
  vowel signs stay inside their word, unlike Python's built-in \\w.
* Languages written without spaces (Japanese, Chinese, Thai) are indexed as
  overlapping character bigrams, a standard trick for CJK retrieval.
"""
import os
import math

import numpy as np
import regex as re

from .config import CJK_LANGS

WORD = re.compile(r"[\p{L}\p{M}]+(?:['’-][\p{L}\p{M}]+)*")
SENT_SPLIT = re.compile(r"(?<=[.!?।。！？])\s*|\n+")
CJK_CHAR = re.compile(r"[\p{Han}\p{Hiragana}\p{Katakana}\p{Thai}ー]")
HEADING = re.compile(r"^==+.*?==+\s*$", re.M)

# Small stop-word lists for the demo languages; other languages fall back to
# IDF, which already down-weights very common words.
STOP = {
    "en": set("the a an and or of to in on for with is are was were be been by as at from that this it its "
              "which who also has have had not but their they he she his her than into such".split()),
    "es": set("el la los las un una unos unas y o de del al en con por para es son fue era ser se que "
              "su sus como más pero lo le les este esta estos estas también".split()),
    "fr": set("le la les un une des et ou de du au aux en dans avec par pour est sont était être se que qui "
              "son sa ses comme plus mais il elle ils elles ce cette ces aussi".split()),
    "hi": set("का की के है हैं था थे और में से को पर एक यह वह भी लिए किया कि जो तथा या ने".split()),
}


def strip_headings(text: str) -> str:
    return HEADING.sub("", text)


def is_cjk(lang: str) -> bool:
    return lang in CJK_LANGS


def words(text: str, lang: str):
    """Surface words (for difficulty features). CJK: individual characters."""
    if is_cjk(lang):
        return CJK_CHAR.findall(text) + [w for w in WORD.findall(text) if not CJK_CHAR.search(w)]
    return WORD.findall(text)


def index_tokens(text: str, lang: str):
    """Tokens used by the BM25 index and queries."""
    text = text.lower()
    if is_cjk(lang):
        toks = []
        for run in re.findall(r"[\p{Han}\p{Hiragana}\p{Katakana}ー]+", text):
            if len(run) == 1:
                toks.append(run)
            toks.extend(run[i:i + 2] for i in range(len(run) - 1))
        toks += [w for w in WORD.findall(text) if not CJK_CHAR.search(w)]
        return toks
    stop = STOP.get(lang, set())
    toks = [w for w in WORD.findall(text) if w not in stop and len(w) > 1]
    st = _stemmer(lang)
    return [st(w) for w in toks] if st else toks


_STEMS = {}
_SNOW = {"en": "english", "es": "spanish", "fr": "french"}


def _stemmer(lang):
    """Opt-in Snowball stemming (LL_STEM=1) for en/es/fr; off by default."""
    if os.environ.get("LL_STEM") != "1" or lang not in _SNOW:
        return None
    if lang not in _STEMS:
        import snowballstemmer
        _STEMS[lang] = snowballstemmer.stemmer(_SNOW[lang]).stemWord
    return _STEMS[lang]


def sentences(text: str):
    return [s for s in SENT_SPLIT.split(strip_headings(text)) if len(s.strip()) > 1]


def features(text: str, lang: str, rare_vocab: set):
    """Language-independent difficulty features for one article.

    rare_vocab is the set of the language's most frequent words; anything
    outside it counts as rare.
    """
    body = strip_headings(text)[:6000]
    sents = sentences(body) or [body]
    ws = words(body, lang)
    n = max(len(ws), 1)
    lw = [w.lower() for w in ws]
    avg_sent = n / len(sents)
    avg_wlen = sum(len(w) for w in ws) / n
    rare = sum(1 for w in lw if w not in rare_vocab) / n
    window = lw[:300]
    ttr = len(set(window)) / max(len(window), 1)
    long_words = sum(1 for w in ws if len(w) >= (4 if is_cjk(lang) else 9)) / n
    digits = len(re.findall(r"\d", body)) / max(len(body), 1)
    parens = body.count("(") / len(sents)
    log_len = math.log(len(text) + 1)
    return [avg_sent, avg_wlen, rare, ttr, long_words, digits, parens, log_len]


FEATURE_NAMES = ["avg_sentence_len", "avg_word_len", "rare_word_share", "type_token_ratio",
                 "long_word_share", "digit_rate", "parens_per_sentence", "log_length"]

# ---- Extended features (CEFRLex-style frequency bands, syllables, clause markers) ----

# Subordinating conjunctions / relative pronouns: a cheap proxy for clause depth.
SUBORD = {
    "en": set("which whom whose although though because whereas while whilst unless whether since "
              "until wherein whereby despite".split()),
    "es": set("cual cuales cuyo cuya cuyos cuyas aunque porque mientras donde cuando si sino "
              "pues según quien quienes".split()),
    "fr": set("dont lequel laquelle lesquels lesquelles auquel duquel quoique lorsque puisque "
              "tandis bien parce afin car".split()),
    "hi": set("जो जिसे जिसका जिसकी जिसके जिन्होंने क्योंकि यद्यपि हालांकि जब तब यदि अगर ताकि जबकि".split()),
    "ja": {"ので", "けれど", "ながら", "ため", "による", "において", "における", "としての", "について"},
}
VOWELS = re.compile(r"[aeiouyáéíóúàèìòùâêîôûäëïöüœæ]+", re.I)
DEVA_VOWEL = re.compile(r"[\u0904-\u0914\u093E-\u094C\u0962\u0963]")
KANJI = re.compile(r"\p{Han}")
COMMA = re.compile(r"[,、،;；，]")

EXT_FEATURE_NAMES = ["syllables_per_word", "core_vocab_share", "mid_band_share", "subord_per_sentence",
                     "commas_per_sentence", "sentence_len_std", "long_sentence_share"]
ALL_FEATURE_NAMES = FEATURE_NAMES + EXT_FEATURE_NAMES


def ext_features(text: str, lang: str, vocab_rank: dict):
    """Extra difficulty features. vocab_rank maps the language's frequent words to their rank."""
    body = strip_headings(text)[:6000]
    sents = sentences(body) or [body]
    ws = words(body, lang)
    n = max(len(ws), 1)
    lw = [w.lower() for w in ws]
    if is_cjk(lang):
        cjk = CJK_CHAR.findall(body)
        syl = len(KANJI.findall(body)) / max(len(cjk), 1)     # kanji density
        sub = sum(body.count(m) for m in SUBORD.get(lang, ())) / len(sents)
    else:
        if lang == "hi":
            syl = sum(max(1, len(DEVA_VOWEL.findall(w)) + 1) for w in ws) / n
        else:
            syl = sum(max(1, len(VOWELS.findall(w))) for w in ws) / n
        sub_set = SUBORD.get(lang, set())
        sub = sum(1 for w in lw if w in sub_set) / len(sents)
    core = sum(1 for w in lw if vocab_rank.get(w, 10 ** 9) < 500) / n
    mid = sum(1 for w in lw if 500 <= vocab_rank.get(w, 10 ** 9) < 3000) / n
    commas = len(COMMA.findall(body)) / len(sents)
    slen = [len(words(s, lang)) for s in sents]
    long_cut = 60 if is_cjk(lang) else 25
    return [syl, core, mid, sub, commas, float(np.std(slen)), sum(1 for x in slen if x > long_cut) / len(slen)]
