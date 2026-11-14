"""Interface text for the Flask app in English and Spanish.

The interface language is independent of the language being learned.
"""

STRINGS = {
    "en": {
        "tagline": "Wikipedia at your reading level",
        "nav_search": "Search", "nav_words": "My words", "nav_profile": "Profile", "ui_label": "Interface",
        "footer": "Articles from Wikipedia, Simple English Wikipedia and Vikidia (CC BY-SA). Ranking: BM25 + level fit.",
        "home_h1": "Read what you love, at your level.",
        "home_p": "LinguaLadder finds Wikipedia articles in the language you're learning that match both your interests and your reading level, and translates any word you highlight.",
        "profile_h": "Your profile", "learning": "I'm learning", "native": "My native language",
        "level": "My reading level", "articles": "articles", "save": "Save and start reading",
        "topics_h": "Topics in the demo corpus",
        "lv_beginner": "Beginner (A1-A2)", "lv_intermediate": "Intermediate (B1-B2)", "lv_advanced": "Advanced (C1+)",
        "lvl_beginner": "Beginner", "lvl_intermediate": "Intermediate", "lvl_advanced": "Advanced",
        "lang_en": "English", "lang_es": "Spanish", "lang_te": "Telugu",
        "search_ph": "Search a topic, e.g. volcano, football, chocolate",
        "typed_native": "typed in my language", "compare": "compare with plain BM25", "search_btn": "Search",
        "target_diff": "Target difficulty", "searched_as": "searched as",
        "ll_ranking": "LinguaLadder ranking", "plain_bm25_h": "Plain BM25 (relevance only)",
        "no_results": "No articles found. Try another word", "or_tick": ", or tick \u201ctyped in my language\u201d",
        "difficulty": "difficulty", "words": "words", "cefr": "CEFR", "rel": "rel", "fit": "fit",
        "too_easy": "Too easy", "too_hard": "Too hard", "just_right": "Just right",
        "fb_up": "Stepping your level up", "fb_down": "Stepping your level down",
        "fb_apply": "Search again to apply.", "fb_target": "target",
        "fb_thanks": "Thanks! Your target difficulty is now {target}.", "fb_prompt": "How was this article?",
        "hint": "Highlight any word or phrase to translate it.", "source": "source",
        "looked_up": "Words you looked up", "translating": "Translating\u2026",
        "unavailable": "Translation unavailable", "in_sentence": "In this sentence:",
        "words_h": "My words", "col_lang": "Language", "col_word": "Word", "col_trans": "Translation",
        "no_words": "No words yet. Highlight words while reading to save them here.",
        "bad_profile": "Invalid profile: choose a supported language and level.",
        "nf_title": "Not found", "nf_h": "Page not found", "err_title": "Error", "err_h": "Something went wrong",
        "back": "Back to LinguaLadder",
        "t_intro_h": "{lang} placement \u00b7 about 3 minutes",
        "t_intro_p": "Two short parts. First, tap the words you know. Some are made up, so only tap the ones you're sure of. Then fill the blank in a few passages. They get harder or easier as you go.",
        "t_start": "Start",
        "t_vocab_h": "Which of these words do you know?",
        "t_vocab_p": "Tap every word you could explain or translate. Leave the rest.",
        "t_continue": "Continue",
        "t_cloze_h": "Fill the blank",
        "t_of": "{i} of {n}",
        "t_skip": "I don't know",
        "t_res_lead": "Your reading level in {lang}",
        "t_res_detail": "{level} \u00b7 vocabulary {vocab}% \u00b7 reading at the {pct}th percentile of articles. Results now aim at this level, and \"Too easy\" or \"Too hard\" on any article fine-tunes it.",
        "t_done": "Start reading",
        "place_link": "Take the placement test",
        "place_again": "Retake the test",
        "place_chip": "Placement result",
        "rec_h": "Recommended topics",
        "rec_sub": "picked for your level",
        "all_topics": "All {n} topics",
        "fewer_topics": "Show fewer",
        "ladder_h": "The ladder for this topic", "ladder_none": "No article at this level yet",
        "next_up": "Next up:", "nothing_harder": "(nothing harder left on this topic)",
        "all_read": "You have read everything on this topic. Try a recommended topic.",
    },
    "es": {
        "tagline": "Wikipedia a tu nivel de lectura",
        "nav_search": "Buscar", "nav_words": "Mis palabras", "nav_profile": "Perfil", "ui_label": "Interfaz",
        "footer": "Art\u00edculos de Wikipedia, Simple English Wikipedia y Vikidia (CC BY-SA). Orden: BM25 + ajuste al nivel.",
        "home_h1": "Lee lo que te gusta, a tu nivel.",
        "home_p": "LinguaLadder encuentra art\u00edculos de Wikipedia en el idioma que est\u00e1s aprendiendo que encajan con tus intereses y con tu nivel de lectura, y traduce cualquier palabra que subrayes.",
        "profile_h": "Tu perfil", "learning": "Estoy aprendiendo", "native": "Mi lengua materna",
        "level": "Mi nivel de lectura", "articles": "art\u00edculos", "save": "Guardar y empezar a leer",
        "topics_h": "Temas del corpus de demostraci\u00f3n",
        "lv_beginner": "Principiante (A1-A2)", "lv_intermediate": "Intermedio (B1-B2)", "lv_advanced": "Avanzado (C1+)",
        "lvl_beginner": "Principiante", "lvl_intermediate": "Intermedio", "lvl_advanced": "Avanzado",
        "lang_en": "Ingl\u00e9s", "lang_es": "Espa\u00f1ol", "lang_te": "Telugu",
        "search_ph": "Busca un tema, p. ej. volc\u00e1n, f\u00fatbol, chocolate",
        "typed_native": "escrito en mi idioma", "compare": "comparar con BM25 simple", "search_btn": "Buscar",
        "target_diff": "Dificultad objetivo", "searched_as": "buscado como",
        "ll_ranking": "Orden de LinguaLadder", "plain_bm25_h": "BM25 simple (solo relevancia)",
        "no_results": "No se encontraron art\u00edculos. Prueba con otra palabra", "or_tick": ", o marca \u00abescrito en mi idioma\u00bb",
        "difficulty": "dificultad", "words": "palabras", "cefr": "MCER", "rel": "rel", "fit": "ajuste",
        "too_easy": "Muy f\u00e1cil", "too_hard": "Muy dif\u00edcil", "just_right": "Justo",
        "fb_up": "Subo tu nivel", "fb_down": "Bajo tu nivel",
        "fb_apply": "Busca de nuevo para aplicarlo.", "fb_target": "objetivo",
        "fb_thanks": "\u00a1Gracias! Tu dificultad objetivo es ahora {target}.", "fb_prompt": "\u00bfQu\u00e9 tal este art\u00edculo?",
        "hint": "Subraya una palabra o frase para traducirla.", "source": "fuente",
        "looked_up": "Palabras que has consultado", "translating": "Traduciendo\u2026",
        "unavailable": "Traducci\u00f3n no disponible", "in_sentence": "En esta frase:",
        "words_h": "Mis palabras", "col_lang": "Idioma", "col_word": "Palabra", "col_trans": "Traducci\u00f3n",
        "no_words": "A\u00fan no hay palabras. Subraya palabras mientras lees para guardarlas aqu\u00ed.",
        "bad_profile": "Perfil no v\u00e1lido: elige un idioma y un nivel admitidos.",
        "nf_title": "No encontrado", "nf_h": "P\u00e1gina no encontrada", "err_title": "Error", "err_h": "Algo sali\u00f3 mal",
        "back": "Volver a LinguaLadder",
        "t_intro_h": "Prueba de nivel de {lang} \u00b7 unos 3 minutos",
        "t_intro_p": "Dos partes cortas. Primero, toca las palabras que conoces. Algunas son inventadas, as\u00ed que toca solo las que tengas claras. Despu\u00e9s, completa el hueco en unos pocos textos. Se vuelven m\u00e1s dif\u00edciles o m\u00e1s f\u00e1ciles seg\u00fan tus respuestas.",
        "t_start": "Empezar",
        "t_vocab_h": "\u00bfCu\u00e1les de estas palabras conoces?",
        "t_vocab_p": "Toca cada palabra que sepas explicar o traducir. Deja las dem\u00e1s.",
        "t_continue": "Continuar",
        "t_cloze_h": "Completa el hueco",
        "t_of": "{i} de {n}",
        "t_skip": "No lo s\u00e9",
        "t_res_lead": "Tu nivel de lectura en {lang}",
        "t_res_detail": "{level} \u00b7 vocabulario {vocab}% \u00b7 lees al nivel del percentil {pct} de los art\u00edculos. Ahora los resultados apuntan a este nivel, y \u00abMuy f\u00e1cil\u00bb o \u00abMuy dif\u00edcil\u00bb en cualquier art\u00edculo lo afina.",
        "t_done": "Empezar a leer",
        "place_link": "Haz la prueba de nivel",
        "place_again": "Repetir la prueba",
        "place_chip": "Resultado de la prueba",
        "rec_h": "Temas recomendados",
        "rec_sub": "elegidos para tu nivel",
        "all_topics": "Los {n} temas",
        "fewer_topics": "Ver menos",
        "ladder_h": "La escalera de este tema", "ladder_none": "A\u00fan no hay art\u00edculo de este nivel",
        "next_up": "Siguiente:", "nothing_harder": "(no queda nada m\u00e1s dif\u00edcil sobre este tema)",
        "all_read": "Ya has le\u00eddo todo sobre este tema. Prueba con un tema recomendado.",
    },
}
UI_LANGS = tuple(STRINGS)
# keys the reader script needs in the page's own language
READER_KEYS = ("translating", "unavailable", "in_sentence", "fb_thanks")


def detect(accept_language):
    """Pick the interface language from an Accept-Language header (Spanish if it comes first)."""
    first = (accept_language or "").split(",")[0].strip().lower()
    return "es" if first.startswith("es") else "en"


def make_t(ui):
    d, en = STRINGS.get(ui, STRINGS["en"]), STRINGS["en"]

    def t(key, **kw):
        s = d.get(key, en.get(key, key))
        return s.format(**kw) if kw else s
    return t


# Language names in Spanish (the English names come from config).
LANG_NAMES_ES = {
    "en": "Ingl\u00e9s", "es": "Espa\u00f1ol", "fr": "Franc\u00e9s", "hi": "Hindi", "ja": "Japon\u00e9s", "te": "Telugu",
    "ta": "Tamil", "zh-CN": "Chino", "ar": "\u00c1rabe", "de": "Alem\u00e1n", "pt": "Portugu\u00e9s", "ko": "Coreano",
    "ru": "Ruso", "it": "Italiano",
}


def lang_name(code, ui, english):
    return LANG_NAMES_ES.get(code, english) if ui == "es" else english


_TOPICS_ES = None


def topic_labels_es():
    """English topic title -> Spanish title (data/topic_labels_es.json), cached."""
    global _TOPICS_ES
    if _TOPICS_ES is None:
        import json
        from .config import DATA_DIR
        f = DATA_DIR / "topic_labels_es.json"
        _TOPICS_ES = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return _TOPICS_ES
