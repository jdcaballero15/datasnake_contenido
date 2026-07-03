"""Validación de la respuesta de Gemini antes de renderizar.

Si no valida, main.py reintenta una vez y si no, cae a plan B.
"""

MIN_CHARS_CAPTION = 400
MAX_CHARS_PORTADA = 60
MAX_HASHTAGS = 5
RANGO_IDEAS = (1, 6)

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
    lo, hi = RANGO_IDEAS
    if not (lo <= len(datos["ideas"]) <= hi):
        raise ValueError(f"{tipo}: {len(datos['ideas'])} ideas fuera de rango")
    if tipo == "tip" and not datos["codigo"].strip():
        raise ValueError("tip: codigo vacío")
