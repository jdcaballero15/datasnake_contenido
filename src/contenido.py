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

PLACAS_POR_TIPO: dict[str, list[list[str]]] = {
    "tip": [["el problema", "el código"], ["por qué funciona"]],
}
"""Cómo se reparten las secciones de UNA idea entre placas del carrusel.

Solo aparece acá el tipo que necesita más de una placa. El tip es el único con
una sola idea, así que sin repartir sus tres secciones quedan apiladas en una
placa que se ve saturada; los demás tipos ya respiran porque emiten una placa
por unidad (una opción, una skill, un cambio).

El orden de los labels dentro de cada grupo, y el de los grupos entre sí, es el
orden en que se ven en el carrusel."""


def grupos_de_placa(tipo: str) -> list[list[str]]:
    """Los grupos de secciones de <tipo>: uno por placa de contenido.

    El default —un único grupo con todos los labels del tipo— es lo que deja a
    novedad, comparativa y rol exactamente como estaban: una placa por idea."""
    return PLACAS_POR_TIPO.get(tipo, [SECCIONES_POR_TIPO[tipo]])


MAX_CHARS_SECCION_SOLA = 520
"""Tope de caracteres para una sección que ocupa su placa sola.

Cuando un grupo de grupos_de_placa tiene un solo label, esa sección no comparte
el panel con nadie: tiene el alto entero de la placa para ella, así que el tope
de MAX_CHARS_SECCION_TEXTO —calculado para dos secciones por panel— la deja
mucho más corta de lo que entra. El valor está medido sobre el PNG renderizado
del peor caso; ver docs/superpowers/plans/2026-07-28-tip-en-dos-placas.md."""


def max_chars_seccion(tipo: str, label: str) -> int:
    """El tope de caracteres del texto de <label> en <tipo>, según comparta
    placa o no.

    Un label que no pertenece a ningún grupo cae al tope conservador: validar()
    ya rechaza los labels inventados por su cuenta, y no es tarea de esta
    función decidir eso."""
    for grupo in grupos_de_placa(tipo):
        if label in grupo:
            return MAX_CHARS_SECCION_SOLA if len(grupo) == 1 else MAX_CHARS_SECCION_TEXTO
    return MAX_CHARS_SECCION_TEXTO


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


def _con_labels(tipo: str, *textos: str) -> list[dict]:
    """Empareja <textos> con los labels de secciones que le tocan a <tipo>, en
    el orden del contrato. Usa secciones_que_redacta_gemini (no
    SECCIONES_POR_TIPO directo) porque en "tip" el label "el código" no viaja
    como texto: esa sección la arma aparte inyectar_codigo_tip, así que acá
    hay que alinear solo contra los labels que SÍ llevan "texto"."""
    labels = secciones_que_redacta_gemini(tipo)
    return [{"label": label, "texto": texto} for label, texto in zip(labels, textos)]


def ideas_desde_item(tipo: str, item: dict) -> list[dict]:
    """Ideas densas armadas SOLO con el material del banco/feed, sin IA (plan B).

    La unidad de idea depende del tipo: una opción (comparativa), una skill (rol),
    el tip entero (tip), el cambio (novedad).

    Los labels salen de SECCIONES_POR_TIPO (vía _con_labels), nunca como
    strings literales acá: como este camino no pasa por contratos.validar,
    hardcodear los labels desincronizaría en silencio las placas del plan B
    si alguien renombra un label en la constante."""
    if tipo == "comparativa":
        return [{
            "titulo": o["nombre"],
            "deck": item["tarea"],
            "secciones": _con_labels(tipo, o["cuando_conviene"], o["donde_duele"]),
        } for o in item["opciones"]]

    if tipo == "rol":
        return [{
            "titulo": s["nombre"],
            "deck": item["gancho"],
            "secciones": _con_labels(tipo, s["por_que"], s["como_practicar"]),
        } for s in item["skills"]]

    if tipo == "tip":
        idea = {
            "titulo": item["titulo"],
            "deck": "",
            "secciones": _con_labels(tipo, item["gancho"], item["explicacion"]),
        }
        inyectar_codigo_tip({"ideas": [idea], "codigo": item["codigo"],
                              "lenguaje": item.get("lenguaje", "sql")})
        return [idea]

    return [{
        "titulo": item["titulo"],
        "deck": item.get("fuente", ""),
        "secciones": _con_labels(
            tipo,
            _limpiar_y_truncar_resumen(item["resumen"]),
            "Una novedad para tener en el radar si trabajás con esta herramienta."),
    }]
