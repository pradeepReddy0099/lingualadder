"""Shared configuration for LinguaLadder."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
MODEL_DIR = DATA_DIR / "models"
for _d in (DATA_DIR, RAW_DIR, MODEL_DIR):
    _d.mkdir(parents=True, exist_ok=True)

USER_AGENT = "LinguaLadder/1.0 (student IR course project; contact psama@wpi.edu)"

# Target languages the demo corpus covers. The code works for any Wikipedia
# language code: add it here and re-run collect.py.
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
}

# Native languages offered for translation (any Google Translate code works).
NATIVE_LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "hi": "Hindi", "ja": "Japanese",
    "te": "Telugu", "ta": "Tamil", "zh-CN": "Chinese", "ar": "Arabic", "de": "German",
    "pt": "Portuguese", "ko": "Korean", "ru": "Russian", "it": "Italian",
}

# Sources of "easy" text, used both as corpus documents and as training labels.
EASY_SOURCES = {
    "en": "https://simple.wikipedia.org/w/api.php",
    "es": "https://es.vikidia.org/w/api.php",
    "fr": "https://fr.vikidia.org/w/api.php",
}

def wiki_api(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"

# Languages written without spaces between words: index character bigrams.
CJK_LANGS = {"ja", "zh", "zh-CN", "zh-TW", "th", "ko_char"}

LEVELS = {
    "beginner": {"label": "Beginner (A1-A2)", "target": 0.20},
    "intermediate": {"label": "Intermediate (B1-B2)", "target": 0.50},
    "advanced": {"label": "Advanced (C1+)", "target": 0.80},
}

# Ranking parameters (tuned in evaluate.py).
ALPHA = 0.5     # weight of relevance vs. level fit
SIGMA = 0.15    # width of the level-fit curve
CANDIDATES = 100

SEED_TOPICS = [
    "Volcano", "Association football", "Frida Kahlo", "Solar System", "Dinosaur",
    "Photosynthesis", "Cricket", "Chocolate", "Coffee", "Internet", "Computer",
    "Artificial intelligence", "Olympic Games", "Guitar", "Pizza", "Elephant",
    "Ocean", "Climate change", "Earthquake", "Moon", "Leonardo da Vinci",
    "Albert Einstein", "Ancient Egypt", "Roman Empire", "Mount Everest",
    "Rainforest", "Butterfly", "Shark", "Tea", "Rice", "Bicycle", "Train",
    "Airplane", "Basketball", "Tennis", "Mahatma Gandhi", "Film", "Painting",
    "Human brain", "Vaccine", "Bird", "Rainbow", "Yoga", "Chess", "Honey bee",
    "Pyramid", "Tiger", "Space exploration", "Music", "Bread",
]
