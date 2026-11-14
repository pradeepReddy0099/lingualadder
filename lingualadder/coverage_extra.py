"""Targeted fill for stubborn coverage gaps: hand-picked related search terms per topic (and language).

python -m lingualadder.coverage_extra     fetch candidates for the current gaps into data/raw/fill_<lang>.jsonl
Then rebuild (python -m lingualadder.build) and re-run python -m lingualadder.coverage.
Candidates come from the easy source (Simple English Wikipedia / Vikidia) and from short regular articles.
"""
import json
from concurrent.futures import ThreadPoolExecutor

from .config import EASY_SOURCES, RAW_DIR, wiki_api
from .coverage import search

EXTRA = {
    "es": {
        "Inca Empire": ["Imperio incaico", "Incas", "Machu Picchu", "Tahuantinsuyo", "Pachacútec", "Cuzco", "Sacsayhuamán", "Quechua", "Perú"],
        "Colombia": ["Bogotá", "Medellín", "Cartagena de Indias", "Historia de Colombia", "Café de Colombia", "Cali", "Barranquilla", "Río Magdalena", "Selección de fútbol de Colombia"],
        "Barcelona": ["Sagrada Familia", "FC Barcelona", "Antoni Gaudí", "Cataluña", "Parque Güell", "Las Ramblas", "Camp Nou", "Montjuïc"],
        "Vegetable": ["Hortaliza", "Verdura", "Zanahoria", "Tomate", "Lechuga", "Cebolla", "Patata", "Huerto", "Pimiento", "Calabaza"],
        "Tourism": ["Turismo", "Turista", "Vacaciones", "Hotel", "Playa", "Excursión", "Agencia de viajes", "Parque temático", "Turismo rural", "Viaje"],
        "Painting": ["Pintura", "Pintor", "Óleo", "Acuarela", "Retrato", "Museo del Prado", "Pablo Picasso", "Diego Velázquez", "Impresionismo", "Cuadro"],
        "Magnetism": ["Imán", "Magnetismo", "Brújula", "Electromagnetismo", "Campo magnético", "Polo magnético"],
        "Carnival": ["Carnaval", "Carnaval de Río de Janeiro", "Disfraz", "Máscara", "Comparsa", "Carnaval de Cádiz", "Carnaval de Venecia", "Carnaval de Barranquilla"],
        "Corn": ["Maíz", "Palomitas de maíz", "Cereal", "Tortilla", "Mazorca", "Elote", "Harina de maíz"],
        "Martial arts": ["Artes marciales", "Judo", "Kárate", "Taekwondo", "Kung-fu", "Aikido", "Capoeira", "Sumo", "Esgrima", "Boxeo"],
        "FC Barcelona": ["Fútbol Club Barcelona", "Lionel Messi", "Camp Nou", "Real Madrid", "Johan Cruyff", "Xavi Hernández", "Liga de fútbol española", "La Masia"],
        "Ship": ["Barco", "Buque", "Velero", "Submarino", "Crucero", "Portaaviones", "Titanic", "Puerto", "Carabela", "Galeón", "Barco de vapor"],
        "Mexico City": ["Ciudad de México", "Zócalo de la Ciudad de México", "Tenochtitlan", "Distrito Federal", "Metro de la Ciudad de México", "Bosque de Chapultepec", "Xochimilco", "Coyoacán", "Teotihuacán"],
        "Virus": ["Virus", "Gripe", "Resfriado", "Vacuna", "Enfermedad", "Bacteria", "Epidemia", "Sarampión", "Varicela", "Coronavirus", "Virus informático"],
        "Space exploration": ["Exploración espacial", "Astronauta", "Cohete", "Luna", "Satélite artificial", "Estación Espacial Internacional", "Apolo 11", "Marte", "Sputnik", "Telescopio espacial"],
    },
    "en": {
        "Gabriel García Márquez": ["Gabriel García Márquez", "One Hundred Years of Solitude", "Colombian writer", "Magic realism", "Nobel Prize in Literature", "Colombia", "Macondo"],
        "Brazil": ["Brazil", "Rio de Janeiro", "São Paulo", "Amazon River", "Brasília", "Carnival", "Portuguese language", "Pelé", "Amazon rainforest"],
        "Photography": ["Photography", "Camera", "Photograph", "Photographer", "Digital camera", "Lens", "Film", "Flash"],
    },
}


def main():
    from .collect import fetch_extract
    from .coverage import report
    cov = report(write=False)
    existing = set()
    for p in RAW_DIR.glob("*.jsonl"):
        for line in open(p, encoding="utf-8"):
            d = json.loads(line); existing.add((d["source"], d["title"]))
    for lang, topics in EXTRA.items():
        easy_url, reg_url = EASY_SOURCES[lang], wiki_api(lang)
        easy_src = "simple.wikipedia" if lang == "en" else f"{lang}.vikidia"
        jobs = []
        for topic, queries in topics.items():
            missing = cov[lang]["gaps"].get(topic)
            if not missing:
                continue
            for q in queries:
                for t in search(easy_url, q, 6):
                    jobs.append((easy_url, t, {"lang": lang, "source": easy_src, "topic": topic, "en_title": None, "easy": 1, "_short": 0}))
                for t in search(reg_url, q, 10):
                    jobs.append((reg_url, t, {"lang": lang, "source": f"{lang}.wikipedia", "topic": topic, "en_title": None, "easy": 0, "_short": 1}))
        seen, uniq = set(), []
        for j in jobs:
            k = (j[2]["source"], j[1], j[2]["topic"])
            if k not in seen and (j[2]["source"], j[1]) not in existing:
                seen.add(k); uniq.append(j)

        def get(j):
            url, title, meta = j
            a = fetch_extract(url, title)
            if not a or (meta["_short"] and len(a["text"].split()) > 700):
                return None
            a.update({k: v for k, v in meta.items() if not k.startswith("_")})
            return a
        n = 0
        with ThreadPoolExecutor(16) as ex, open(RAW_DIR / f"fill_{lang}.jsonl", "a", encoding="utf-8") as f:
            for a in ex.map(get, uniq):
                if a:
                    f.write(json.dumps(a, ensure_ascii=False) + "\n"); n += 1
        print(f"{lang}: {len(uniq)} candidates, {n} fetched and kept")


if __name__ == "__main__":
    main()
