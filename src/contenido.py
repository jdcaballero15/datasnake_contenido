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


def normalizar_ideas(tipo: str, red: dict) -> list[dict]:
    """Puente: Gemini todavía devuelve {titulo, texto}. Lo envuelve en el modelo
    denso para que la plantilla no tenga que saber de qué época viene el dato.
    Se elimina en la etapa 2, cuando Gemini devuelva secciones."""
    ideas = []
    for idea in red.get("ideas", []):
        if "secciones" in idea:
            ideas.append(idea)
            continue
        ideas.append({
            "titulo": idea.get("titulo", ""),
            "deck": idea.get("deck", ""),
            "secciones": [{"label": SECCIONES_POR_TIPO[tipo][0],
                           "texto": idea.get("texto", "")}],
        })
    if tipo == "tip" and red.get("codigo") and ideas:
        ideas[0]["secciones"].append({
            "label": "el código",
            "codigo": red["codigo"],
            "lenguaje": red.get("lenguaje", "sql"),
        })
    return ideas
