"""Validación de la respuesta de Gemini antes de renderizar.

Si no valida, main.py reintenta una vez y si no, cae a plan B.
"""

from src.contenido import MAX_CHARS_SECCION_TEXTO, secciones_que_redacta_gemini

MIN_CHARS_CAPTION = 400
MAX_CHARS_PORTADA = 60
MAX_HASHTAGS = 5
RANGO_IDEAS = (1, 6)

# El prompt pide "titulo" de 1-3 palabras (entra gigante, Anton 94px) y "deck"
# de una oración (Archivo 38px, max-width 900px). El peor caso real de los
# bancos hoy es 54 chars de titulo y 76 de deck (ver datos/*.json); estos
# topes dejan margen sin permitir que Gemini se vaya tan de largo que la
# placa desborde (.plate tiene overflow:hidden: lo que se pasa se corta).
MAX_CHARS_TITULO_IDEA = 80
MAX_CHARS_DECK = 120

_CAMPOS = {
    "novedad": ("titulo_portada", "ideas", "caption", "hashtags"),
    "comparativa": ("titulo_portada", "ideas", "caption", "hashtags"),
    "rol": ("titulo_portada", "ideas", "caption", "hashtags"),
    "tip": ("titulo_portada", "ideas", "codigo", "caption", "hashtags"),
}


def validar(tipo: str, datos: dict) -> None:
    faltan = [c for c in _CAMPOS[tipo] if c not in datos]
    if faltan:
        raise ValueError(f"{tipo}: faltan campos {faltan}")
    if len(datos["caption"]) < MIN_CHARS_CAPTION:
        raise ValueError(f"{tipo}: caption corto ({len(datos['caption'])} chars)")
    if len(datos["titulo_portada"]) > MAX_CHARS_PORTADA:
        raise ValueError(f"{tipo}: titulo_portada largo")
    if len(datos["hashtags"]) > MAX_HASHTAGS:
        raise ValueError(f"{tipo}: demasiados hashtags")
    if tipo == "tip":
        if len(datos["ideas"]) != 1:
            raise ValueError(
                f"tip: debe traer exactamente 1 idea (trajo {len(datos['ideas'])})")
    else:
        lo, hi = RANGO_IDEAS
        if not (lo <= len(datos["ideas"]) <= hi):
            raise ValueError(f"{tipo}: {len(datos['ideas'])} ideas fuera de rango")
    esperadas = secciones_que_redacta_gemini(tipo)
    for i, idea in enumerate(datos["ideas"], start=1):
        if not isinstance(idea, dict):
            raise ValueError(f"{tipo}: idea {i} no es un objeto ({idea!r})")
        secciones = idea.get("secciones", [])
        # Defensa en profundidad: si Gemini manda basura con una forma inesperada
        # (p.ej. "secciones" como lista de strings, o un "texto" que no es str),
        # esto tiene que ser un ValueError -no un AttributeError/TypeError de
        # .get()/.strip() sobre el tipo equivocado-, porque redactar_pieza solo
        # atrapa (GeminiError, ValueError, KeyError, TypeError) antes de caer a
        # plan B; un AttributeError se escapa y voltea todo el lote.
        if not isinstance(secciones, list) or not all(isinstance(s, dict) for s in secciones):
            raise ValueError(
                f"{tipo}: idea {i} tiene 'secciones' mal formadas, se esperaba una "
                f"lista de objetos {{label, texto}} (llegó {secciones!r})")
        labels = [seccion.get("label") for seccion in secciones]
        if labels != esperadas:
            raise ValueError(
                f"{tipo}: idea {i} tiene secciones {labels!r}, se esperaba "
                f"exactamente {esperadas!r} en ese orden (revisá labels y orden)")
        for seccion in secciones:
            texto = seccion.get("texto", "")
            if not isinstance(texto, str) or not texto.strip():
                raise ValueError(
                    f"{tipo}: idea {i} tiene una sección vacía o con 'texto' inválido "
                    f"({texto!r})")
            if len(texto) > MAX_CHARS_SECCION_TEXTO:
                raise ValueError(
                    f"{tipo}: idea {i} tiene 'texto' de sección '{seccion.get('label')}' "
                    f"muy largo ({len(texto)} > {MAX_CHARS_SECCION_TEXTO} chars, se corta "
                    "en la placa)")
        titulo_idea = idea.get("titulo", "")
        if not isinstance(titulo_idea, str) or len(titulo_idea) > MAX_CHARS_TITULO_IDEA:
            raise ValueError(
                f"{tipo}: idea {i} tiene 'titulo' inválido o muy largo ({titulo_idea!r})")
        deck = idea.get("deck", "")
        if not isinstance(deck, str) or len(deck) > MAX_CHARS_DECK:
            raise ValueError(f"{tipo}: idea {i} tiene 'deck' inválido o muy largo ({deck!r})")
    if tipo == "tip" and not datos["codigo"].strip():
        raise ValueError("tip: codigo vacío")
