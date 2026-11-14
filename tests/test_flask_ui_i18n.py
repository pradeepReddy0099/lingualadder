import re
from pathlib import Path

from app import app
from lingualadder import flask_i18n as F


def test_same_keys_and_placeholders():
    en, es = F.STRINGS["en"], F.STRINGS["es"]
    assert set(en) == set(es)
    for k in en:
        assert re.findall(r"\{\w+\}", en[k]) == re.findall(r"\{\w+\}", es[k]), k
        assert es[k].strip()


def test_every_template_key_exists():
    used = set()
    for f in Path("templates").glob("*.html"):
        used |= set(re.findall(r"t\('([a-z_0-9]+)'[,)]", f.read_text(encoding="utf-8")))
    used |= {"lv_beginner", "lv_intermediate", "lv_advanced", "lvl_beginner", "lvl_intermediate", "lvl_advanced"}
    assert used <= set(F.STRINGS["en"]), used - set(F.STRINGS["en"])
    assert set(F.READER_KEYS) <= set(F.STRINGS["en"])


def test_detect():
    assert F.detect("es-ES,es;q=0.9,en;q=0.8") == "es"
    assert F.detect("en-US,en;q=0.9") == "en"
    assert F.detect(None) == "en"


def test_spanish_interface_pages():
    c = app.test_client()
    r = c.get("/", headers={"Accept-Language": "es-MX,es"})
    html = r.get_data(as_text=True)
    assert 'lang="es"' in html and "Lee lo que te gusta" in html and "Guardar y empezar a leer" in html
    assert "Ingl\u00e9s" in html  # language names in Spanish
    assert "Fotograf\u00eda" in html  # Spanish topic labels
    c.post("/", data={"target": "es", "native": "en", "level": "beginner"}, headers={"Accept-Language": "es"})
    r = c.get("/search?q=volcan", headers={"Accept-Language": "es"})
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "Muy f\u00e1cil" in html and "Dificultad objetivo" in html
    assert "Too easy" not in html


def test_switch_and_english_default():
    c = app.test_client()
    c.get("/ui/es")
    assert "Lee lo que te gusta" in c.get("/", headers={"Accept-Language": "en"}).get_data(as_text=True)
    c.get("/ui/en")
    html = c.get("/", headers={"Accept-Language": "es"}).get_data(as_text=True)
    assert "Read what you love" in html
    assert c.get("/ui/fr").status_code == 404


def test_error_pages_translated():
    c = app.test_client()
    c.get("/ui/es")
    r = c.get("/nope")
    assert r.status_code == 404 and "P\u00e1gina no encontrada" in r.get_data(as_text=True)


def test_reader_page_spanish():
    c = app.test_client()
    c.post("/", data={"target": "es", "native": "en", "level": "beginner"})
    c.get("/ui/es")
    from app import ENGINE
    d = ENGINE.docs["es"][0]
    r = c.get("/read/es/" + d["id"])
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "Subraya una palabra" in html and "Traduciendo" in html
