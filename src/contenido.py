"""Modelo de contenido de una placa densa: título + deck + secciones etiquetadas.

Los labels de sección son FIJOS por tipo y viven acá: ni el banco ni Gemini los
eligen. Eso es lo que hace que el carrusel se lea igual semana a semana.
"""

import html
import re

MAX_CHARS_SECCION_TEXTO = 260
"""Tope de caracteres para el "texto" de una sección de placa. La placa
(.plate) tiene overflow:hidden: lo que se pasa de largo se corta, no se ve.
El panel de la placa de contenido renderiza el cuerpo a 33px con ~850px de
ancho útil (ver plantillas/_estilos.html, .section-text); el peor caso real
de los bancos hoy es una idea entera (título + 2 secciones) de ~310
caracteres, así que 260 por sección deja margen sin desbordar. Lo usan tanto
contratos.validar (respuesta de Gemini) como el truncado del resumen crudo de
RSS en el plan B de "novedad" (_limpiar_y_truncar_resumen más abajo), para
que ambos caminos respeten el mismo límite físico."""

_TAG_HTML = re.compile(r"<[^>]+>")
_ESPACIOS = re.compile(r"\s+")


def _limpiar_y_truncar_resumen(texto: str, largo: int = MAX_CHARS_SECCION_TEXTO) -> str:
    """Resúmenes de RSS (entry.summary de feedparser) sin HTML crudo y
    acotados al largo que entra en la placa.

    feedparser no limpia el HTML del feed: con autoescape la placa mostraría
    literalmente "<p>Today we are announcing...</p>". Y los feeds suelen
    mandar resúmenes de ~1.100 caracteres, muy por encima de lo que entra en
    el panel. El corte respeta el límite de palabra (no parte una palabra al
    medio) y cierra con elipsis para que quede claro que sigue en el link."""
    sin_tags = _TAG_HTML.sub(" ", texto)
    limpio = _ESPACIOS.sub(" ", html.unescape(sin_tags)).strip()
    if len(limpio) <= largo:
        return limpio
    corte = limpio[:largo].rsplit(" ", 1)[0].rstrip(" .,;:-")
    return f"{corte}…"


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


def secciones_que_redacta_gemini(tipo: str) -> list[str]:
    """Los labels que Gemini debe devolver para <tipo>, en el orden esperado.

    Coincide con SECCIONES_POR_TIPO salvo para "tip": ahí Gemini no escribe
    "el código" como sección (viaja aparte en los campos "codigo"/"lenguaje";
    ver inyectar_codigo_tip), así que ese label no forma parte de lo que se le
    exige a la respuesta del modelo."""
    labels = SECCIONES_POR_TIPO[tipo]
    if tipo == "tip":
        pos = labels.index("el código")
        return labels[:pos] + labels[pos + 1:]
    return labels


def inyectar_codigo_tip(datos: dict) -> None:
    """Arma la sección "el código" de la (única) idea de un tip y la inserta
    en la posición que fija SECCIONES_POR_TIPO, a partir de los campos
    "codigo"/"lenguaje" de datos.

    Gemini no escribe esta sección como texto (ver prompt_tip / secciones_que_
    redacta_gemini): el snippet viaja aparte. Esta función es la única fuente
    de esa lógica — la usan tanto la respuesta de Gemini (vía main.redactar_
    pieza) como el plan B (ideas_desde_item, más abajo)."""
    secciones = datos["ideas"][0]["secciones"]
    pos = SECCIONES_POR_TIPO["tip"].index("el código")
    secciones.insert(pos, {"label": "el código", "codigo": datos["codigo"],
                            "lenguaje": datos.get("lenguaje", "sql")})


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
        idea = {
            "titulo": item["titulo"],
            "deck": "",
            "secciones": [
                {"label": "el problema", "texto": item["gancho"]},
                {"label": "por qué funciona", "texto": item["explicacion"]},
            ],
        }
        inyectar_codigo_tip({"ideas": [idea], "codigo": item["codigo"],
                              "lenguaje": item.get("lenguaje", "sql")})
        return [idea]

    return [{
        "titulo": item["titulo"],
        "deck": item.get("fuente", ""),
        "secciones": [
            {"label": "qué cambió", "texto": _limpiar_y_truncar_resumen(item["resumen"])},
            {"label": "por qué importa",
             "texto": "Una novedad para tener en el radar si trabajás con esta herramienta."},
        ],
    }]
