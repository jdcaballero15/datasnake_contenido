"""Orquestador: una corrida = el lote semanal (1 novedad + 2 evergreen).

    python -m src.main               # corrida real (necesita GEMINI_API_KEY)
    python -m src.main --dry-run     # sin red: piezas de muestra con textos fijos
"""

import argparse
import json
import logging
import random
import sys
import time
from datetime import date

from src import contenido, exportar
from src.config import (CTA_COMPARTIR, CTA_GUARDAR, ESLOGAN, HASHTAGS_DEFAULT,
                        Config, PORTADA_VARIANTES, get_config)
from src.fuentes import feeds
from src.fuentes.bancos import registrar_usados, seleccionar
from src.redaccion import prompts
from src.redaccion.contratos import validar
from src.redaccion.gemini import GeminiError, generar_json
from src.render.renderer import Renderer
from src.video.reel_slideshow import generar_reel

log = logging.getLogger("datasnake")

# tipo → (nombre del banco | None si viene de feeds, función de prompt)
TIPOS = {
    "novedad": (None, prompts.prompt_novedad),
    "comparativa": ("comparativas", prompts.prompt_comparativa),
    "rol": ("roles", prompts.prompt_rol),
    "tip": ("tips", prompts.prompt_tip),
}


def variante_portada(fecha: date) -> str:
    """Devuelve la variante de portada correspondiente a la fecha del lote."""
    indice = (fecha - date(2026, 7, 20)).days % len(PORTADA_VARIANTES)
    return f"cover-{PORTADA_VARIANTES[indice]}"


def plan_dia(cfg: Config, seed: int, novedad: dict | None) -> list[dict]:
    """PIEZAS_POR_DIA piezas, novedad-first: 1 novedad si hay, el resto evergreen
    rotando por seed sin repetir. Nunca un lote vacío (mínimo 1 evergreen)."""
    total = max(1, cfg.piezas_por_dia)
    rnd = random.Random(seed)
    tipos_ev = list(cfg.tipos_evergreen)
    rnd.shuffle(tipos_ev)
    n_novedad = 1 if novedad else 0
    n_evergreen = max(0, total - n_novedad)
    elegidos_ev = [tipos_ev[i % len(tipos_ev)] for i in range(n_evergreen)]

    piezas: list[dict] = []
    if novedad:
        piezas.append({"tipo": "novedad", "item": {**novedad, "id": novedad["id"]}})
    for i, tipo in enumerate(elegidos_ev):
        banco, _ = TIPOS[tipo]
        item = seleccionar(cfg, banco, 1, seed + 1 + i)[0]
        piezas.append({"tipo": tipo, "item": item})
    return piezas


def plan_b(tipo: str, item: dict) -> dict:
    """Redacción local sin IA: caption decente + ideas densas desde el propio item."""
    ideas = contenido.ideas_desde_item(tipo, item)
    base = {"hashtags": list(HASHTAGS_DEFAULT), "plan_b": True, "ideas": ideas}
    if tipo == "novedad":
        cuerpo = (f"{item['titulo']}.\n\n{item['resumen']}\n\n"
                  "Una novedad para tener en el radar si trabajás con esta herramienta. "
                  "Probala en tu próximo proyecto y fijate qué te ahorra.")
        return {**base, "titulo_portada": item["titulo"][:60].upper(), "caption": cuerpo}
    if tipo == "comparativa":
        opciones = " ".join(f"{o['nombre']}: {o['cuando_conviene']}" for o in item["opciones"])
        cuerpo = f"{item['tarea']}: no hay una sola respuesta.\n\n{opciones}\n\n{item['veredicto']}"
        return {**base, "titulo_portada": item["tarea"][:60].upper(), "caption": cuerpo}
    if tipo == "rol":
        skills = ", ".join(s["nombre"] for s in item["skills"])
        cuerpo = (f"{item['rol']}: {item['gancho']}\n\n"
                  f"Skills clave: {skills}.\n\n"
                  f"Herramientas: {', '.join(item['herramientas'])}. "
                  "Si apuntás a este rol, arrancá por lo que más se repite en las búsquedas.")
        return {**base, "titulo_portada": item["rol"].upper(), "caption": cuerpo}
    cuerpo = (f"{item['titulo']}.\n\n{item['explicacion']}\n\n"
              "Guardá el snippet y adaptalo a tus tablas. Pequeños trucos así "
              "te ahorran horas en el día a día con datos.")
    return {**base, "titulo_portada": item["titulo"][:60].upper(),
            "codigo": item["codigo"], "lenguaje": item.get("lenguaje", "sql"), "caption": cuerpo}


def redactar_pieza(tipo: str, item: dict, cfg: Config) -> dict:
    _, prompt_de = TIPOS[tipo]
    for intento in range(2):
        try:
            datos = generar_json(prompt_de(item), cfg.gemini_api_key)
            validar(tipo, datos)
            if tipo == "tip":
                contenido.inyectar_codigo_tip(datos)
            return datos
        except (GeminiError, ValueError, KeyError, TypeError) as e:
            log.warning("Redacción de %s falló (intento %d): %s", tipo, intento + 1, e)
    log.warning("Gemini no disponible para %s: plan B", tipo)
    return plan_b(tipo, item)


def armar_caption(cuerpo: str, hashtags: list[str]) -> str:
    tags = " ".join(f"#{h.lstrip('#')}" for h in hashtags[:5])
    return f"{cuerpo.rstrip()}\n\n{CTA_COMPARTIR}\n{CTA_GUARDAR}\n\n{tags}"


def construir_placas(tipo: str, red: dict, variante_cover: str = "cover-green") -> list[dict]:
    tag = {"novedad": "Novedad", "comparativa": "Comparativa",
           "rol": "Carrera en data", "tip": "Tip"}[tipo]
    palabra = contenido.KICKER_POR_TIPO[tipo]

    placas = [{
        "plantilla": "portada",
        "tag": tag,
        "titulo": red["titulo_portada"],
        "subtitulo": red.get("subtitulo", ESLOGAN),
        "variant": variante_cover,
    }]
    for i, idea in enumerate(red["ideas"], start=1):
        placas.append({
            "plantilla": "contenido",
            "kicker": f"{palabra} {i:02d}",
            "titulo": idea["titulo"],
            "deck": idea.get("deck", ""),
            "secciones": idea["secciones"],
            # cada 3ª idea sale en placa clara: es el ritmo que evita que el
            # carrusel se lea como un bloque oscuro uniforme
            "variant": "light" if i % 3 == 0 else "dark",
        })
    placas.append({"plantilla": "cierre", "variant": "close"})

    total = len(placas)
    for i, placa in enumerate(placas, start=1):
        placa["slide_index"] = i
        placa["slide_total"] = total
    return placas


def armar_pieza(indice, tipo, item, red, cfg, renderer, lote_dia, variante_cover):
    carpeta = lote_dia / f"{indice:02d}-{tipo}"
    carpeta.mkdir(parents=True, exist_ok=True)
    for i, ctx in enumerate(construir_placas(tipo, red, variante_cover), start=1):
        renderer.render_placa(ctx, carpeta / f"{i:02d}.png")
    generar_reel(carpeta, cfg, seed=indice)  # opcional; None si no se puede
    (carpeta / "caption.txt").write_text(
        armar_caption(red["caption"], red.get("hashtags", HASHTAGS_DEFAULT)), encoding="utf-8")
    (carpeta / "meta.json").write_text(json.dumps({
        "titulo": red.get("titulo_portada", "").replace("\n", " "), "tipo": tipo,
        "id": item.get("id", ""), "plan_b": bool(red.get("plan_b")),
        "fecha": str(date.today()),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return carpeta


DRY_RUN = {
    "novedad": {
        "titulo_portada": "LO NUEVO\nDE POWER BI",
        "ideas": [{
            "titulo": "COPILOT EN DAX",
            "deck": "Escribís la medida en castellano y te la devuelve en DAX.",
            "secciones": [
                {"label": "qué cambió", "texto": "El panel de medidas ahora acepta lenguaje natural: describís el cálculo y Copilot arma la expresión DAX."},
                {"label": "por qué importa", "texto": "El cuello de botella de un tablero rara vez es el gráfico: es la medida que nadie se acuerda cómo escribir."},
            ],
        }],
        "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT,
    },
    "comparativa": {
        "titulo_portada": "EXCEL VS\nPYTHON",
        "ideas": [
            {"titulo": "EXCEL", "deck": "Limpiar 10.000 filas con nulos y duplicados.",
             "secciones": [
                 {"label": "cuándo conviene", "texto": "Es una limpieza de una sola vez y querés verla con los ojos."},
                 {"label": "dónde duele", "texto": "Son ocho pasos manuales que nadie documenta: la semana que viene los repetís de memoria."}]},
            {"titulo": "PYTHON", "deck": "Limpiar 10.000 filas con nulos y duplicados.",
             "secciones": [
                 {"label": "cuándo conviene", "texto": "La limpieza se repite: tres líneas que corrés igual todos los meses."},
                 {"label": "dónde duele", "texto": "Necesitás el entorno armado y que alguien más pueda correrlo."}]},
        ],
        "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT,
    },
    "rol": {
        "titulo_portada": "DATA\nANALYST",
        "ideas": [
            {"titulo": "SQL", "deck": "El puente entre los datos crudos y la decisión.",
             "secciones": [
                 {"label": "por qué te la piden", "texto": "Es el idioma en el que están los datos: sin SQL dependés de que alguien te pase un export."},
                 {"label": "cómo la practicás", "texto": "Agarrá una base pública y respondé preguntas de negocio sin exportar a Excel."}]},
            {"titulo": "POWER BI", "deck": "El puente entre los datos crudos y la decisión.",
             "secciones": [
                 {"label": "por qué te la piden", "texto": "Nadie decide mirando una tabla: el dashboard es el formato en el que tu trabajo se consume."},
                 {"label": "cómo la practicás", "texto": "Rehacé como dashboard un reporte que hoy vive en Excel, con filtros y una medida propia."}]},
            {"titulo": "COMUNICAR", "deck": "El puente entre los datos crudos y la decisión.",
             "secciones": [
                 {"label": "por qué te la piden", "texto": "Un análisis que no se entiende no existe: te miden por la decisión que gatillaste."},
                 {"label": "cómo la practicás", "texto": "Contá cada análisis en tres frases: qué preguntaste, qué encontraste, qué habría que hacer."}]},
        ],
        "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT,
    },
    "tip": {
        "titulo_portada": "TOP N\nEN SQL",
        "ideas": [{
            "titulo": "TOP N EN SQL",
            "deck": "",
            "secciones": [
                {"label": "el problema", "texto": "Sacar el top 3 por categoría sin anidar tres subconsultas."},
                {"label": "el código", "codigo": "SELECT *\nFROM (\n  SELECT *,\n    ROW_NUMBER() OVER (\n      PARTITION BY categoria ORDER BY ventas DESC) AS rn\n  FROM ventas\n) t\nWHERE rn <= 3;", "lenguaje": "sql"},
                {"label": "por qué funciona", "texto": "ROW_NUMBER numera dentro de cada grupo; filtrás rn <= 3 y tenés el top por categoría en una sola pasada."},
            ],
        }],
        "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT,
    },
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Genera el lote semanal de Data Snake")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    cfg = get_config()
    hoy = date.today()
    variante_cover = variante_portada(hoy)
    lote_dia = cfg.dir_salida / f"lote-{hoy:%Y-%m-%d}"

    if args.dry_run:
        piezas = [{"tipo": t, "item": {"id": "dry"}} for t in TIPOS]
        redacciones = [DRY_RUN[p["tipo"]] for p in piezas]
        novedad = None
    else:
        seed = hoy.toordinal()
        novedad = feeds.elegir_novedad(cfg)
        piezas = plan_dia(cfg, seed, novedad)
        redacciones = []
        for p in piezas:
            redacciones.append(redactar_pieza(p["tipo"], p["item"], cfg))
            time.sleep(cfg.pausa_entre_llamadas)

    fallidas = 0
    with Renderer(cfg) as renderer:
        for i, (pieza, red) in enumerate(zip(piezas, redacciones), start=1):
            try:
                carpeta = armar_pieza(i, pieza["tipo"], pieza["item"], red, cfg, renderer, lote_dia, variante_cover)
                log.info("Pieza %02d lista: %s", i, carpeta.name)
            except Exception as e:  # noqa: BLE001
                fallidas += 1
                log.error("Pieza %02d (%s) falló: %s", i, pieza["tipo"], e)

    if lote_dia.exists():
        exportar.exportar(lote_dia, cfg.dir_salida / "ParaSubir" / lote_dia.name)

    if not args.dry_run:
        if novedad:
            feeds.registrar_vista(cfg, novedad["id"])
        for tipo, (banco, _) in TIPOS.items():
            if banco:
                ids = [p["item"]["id"] for p in piezas if p["tipo"] == tipo]
                registrar_usados(cfg, banco, ids)

    log.info("Lote %s: %d piezas, %d fallidas", lote_dia.name, len(piezas), fallidas)
    return 0 if fallidas < len(piezas) else 1


if __name__ == "__main__":
    sys.exit(main())
