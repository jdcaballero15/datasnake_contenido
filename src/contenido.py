"""Modelo de contenido de una placa densa: título + deck + secciones etiquetadas.

Los labels de sección son FIJOS por tipo y viven acá: ni el banco ni Gemini los
eligen. Eso es lo que hace que el carrusel se lea igual semana a semana.
"""

# Cada placa de contenido de una pieza es "una unidad" del tipo:
#   novedad → un cambio | comparativa → una opción | rol → una skill | tip → el tip
SECCIONES_POR_TIPO: dict[str, list[str]] = {
    "novedad": ["qué cambió", "por qué importa"],
    "comparativa": ["cuándo conviene", "dónde duele"],
    "rol": ["por qué te la piden", "cómo la practicás"],
    "tip": ["el problema", "el código", "por qué funciona"],
}

KICKER_POR_TIPO: dict[str, str] = {
    "novedad": "cambio",
    "comparativa": "opción",
    "rol": "skill",
    "tip": "tip",
}


def ideas_desde_item(tipo: str, item: dict) -> list[dict]:
    """Ideas densas armadas SOLO con el material del banco/feed, sin IA (plan B).

    La unidad de idea depende del tipo: una opción (comparativa), una skill (rol),
    el tip entero (tip), el cambio (novedad)."""
    if tipo == "comparativa":
        return [{
            "titulo": o["nombre"],
            "deck": item["tarea"],
            "secciones": [
                {"label": "cuándo conviene", "texto": o["cuando_conviene"]},
                {"label": "dónde duele", "texto": o["donde_duele"]},
            ],
        } for o in item["opciones"]]

    if tipo == "rol":
        return [{
            "titulo": s["nombre"],
            "deck": item["gancho"],
            "secciones": [
                {"label": "por qué te la piden", "texto": s["por_que"]},
                {"label": "cómo la practicás", "texto": s["como_practicar"]},
            ],
        } for s in item["skills"]]

    if tipo == "tip":
        return [{
            "titulo": item["titulo"],
            "deck": "",
            "secciones": [
                {"label": "el problema", "texto": item["gancho"]},
                {"label": "el código", "codigo": item["codigo"],
                 "lenguaje": item.get("lenguaje", "sql")},
                {"label": "por qué funciona", "texto": item["explicacion"]},
            ],
        }]

    return [{
        "titulo": item["titulo"],
        "deck": item.get("fuente", ""),
        "secciones": [
            {"label": "qué cambió", "texto": item["resumen"]},
            {"label": "por qué importa",
             "texto": "Una novedad para tener en el radar si trabajás con esta herramienta."},
        ],
    }]
