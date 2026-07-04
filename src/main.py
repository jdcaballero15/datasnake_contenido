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

from src import exportar
from src.config import (CTA_COMPARTIR, CTA_GUARDAR, HASHTAGS_DEFAULT, Config,
                        get_config)
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


def plan_semana(cfg: Config, seed: int, novedad: dict | None) -> list[dict]:
    """1 novedad (si hay) + 2 evergreen rotando por seed. Si no hay novedad,
    ese slot cae a un evergreen extra (nunca semana vacía)."""
    rnd = random.Random(seed)
    tipos_ev = list(cfg.tipos_evergreen)
    rnd.shuffle(tipos_ev)
    n_evergreen = cfg.mix["evergreen"] + (0 if novedad else cfg.mix["novedad"])
    elegidos_ev = (tipos_ev * 3)[:n_evergreen]

    piezas: list[dict] = []
    if novedad:
        piezas.append({"tipo": "novedad", "item": {**novedad, "id": novedad["id"]}})
    for i, tipo in enumerate(elegidos_ev):
        banco, _ = TIPOS[tipo]
        item = seleccionar(cfg, banco, 1, seed + 1 + i)[0]
        piezas.append({"tipo": tipo, "item": item})
    return piezas


def plan_b(tipo: str, item: dict) -> dict:
    """Redacción local sin IA: caption decente a partir del propio item."""
    base = {"hashtags": list(HASHTAGS_DEFAULT), "plan_b": True}
    if tipo == "novedad":
        cuerpo = (f"{item['titulo']}.\n\n{item['resumen']}\n\n"
                  "Una novedad para tener en el radar si trabajás con esta herramienta. "
                  "Probala en tu próximo proyecto y fijate qué te ahorra.")
        return {**base, "titulo_portada": item["titulo"][:60].upper(),
                "ideas": [{"titulo": "Qué salió", "texto": item["resumen"][:200]}],
                "caption": cuerpo}
    if tipo == "comparativa":
        ideas = [{"titulo": f"Opción {i+1}", "texto": o} for i, o in enumerate(item["opciones"])]
        cuerpo = (f"{item['tarea']}: no hay una sola respuesta.\n\n" +
                  " ".join(item["opciones"]) + f"\n\n{item['veredicto']}")
        return {**base, "titulo_portada": item["tarea"][:60].upper(), "ideas": ideas, "caption": cuerpo}
    if tipo == "rol":
        ideas = [{"titulo": "Skills", "texto": ", ".join(item["skills"])},
                 {"titulo": "Herramientas", "texto": ", ".join(item["herramientas"])}]
        cuerpo = (f"{item['rol']}: {item['gancho']}\n\n"
                  f"Skills clave: {', '.join(item['skills'])}.\n\n"
                  f"Herramientas: {', '.join(item['herramientas'])}. "
                  "Si apuntás a este rol, arrancá por lo que más se repite en las búsquedas.")
        return {**base, "titulo_portada": item["rol"].upper(), "ideas": ideas, "caption": cuerpo}
    # tip
    cuerpo = (f"{item['titulo']}.\n\n{item['explicacion']}\n\n"
              "Guardá el snippet y adaptalo a tus tablas. Pequeños trucos así "
              "te ahorran horas en el día a día con datos.")
    return {**base, "titulo_portada": item["titulo"][:60].upper(),
            "ideas": [{"titulo": "Cómo funciona", "texto": item["explicacion"]}],
            "codigo": item["codigo"], "lenguaje": item["lenguaje"], "caption": cuerpo}


def redactar_pieza(tipo: str, item: dict, cfg: Config) -> dict:
    _, prompt_de = TIPOS[tipo]
    for intento in range(2):
        try:
            datos = generar_json(prompt_de(item), cfg.gemini_api_key)
            validar(tipo, datos)
            return datos
        except (GeminiError, ValueError, KeyError, TypeError) as e:
            log.warning("Redacción de %s falló (intento %d): %s", tipo, intento + 1, e)
    log.warning("Gemini no disponible para %s: plan B", tipo)
    return plan_b(tipo, item)


def armar_caption(cuerpo: str, hashtags: list[str]) -> str:
    tags = " ".join(f"#{h.lstrip('#')}" for h in hashtags[:5])
    return f"{cuerpo.rstrip()}\n\n{CTA_COMPARTIR}\n{CTA_GUARDAR}\n\n{tags}"


def construir_placas(tipo: str, red: dict) -> list[dict]:
    tag = {"novedad": "Novedad", "comparativa": "Comparativa",
           "rol": "Carrera en data", "tip": "Tip"}[tipo]
    plantilla_idea = "comparativa" if tipo == "comparativa" else "idea"
    placas = [{
        "plantilla": "portada",
        "tag": tag,
        "titulo": red["titulo_portada"],
        "variant": "cover",
    }]
    for i, b in enumerate(red["ideas"], start=1):
        placas.append({
            "plantilla": plantilla_idea,
            "numero": i,
            "titulo": b["titulo"],
            "texto": b["texto"],
            "variant": "light" if tipo == "comparativa" and i == len(red["ideas"]) else "dark",
            "module_label": "cuándo conviene" if tipo == "comparativa" else "qué resuelve",
        })
    if tipo == "tip" and red.get("codigo"):
        placas.append({
            "plantilla": "codigo",
            "lenguaje": red.get("lenguaje", "sql"),
            "codigo": red["codigo"],
            "variant": "code",
        })
    placas.append({"plantilla": "cierre", "variant": "close"})

    total = len(placas)
    for i, placa in enumerate(placas, start=1):
        placa["slide_index"] = i
        placa["slide_total"] = total
    return placas


def armar_pieza(indice, tipo, item, red, cfg, renderer, lote_semana):
    carpeta = lote_semana / f"{indice:02d}-{tipo}"
    carpeta.mkdir(parents=True, exist_ok=True)
    for i, ctx in enumerate(construir_placas(tipo, red), start=1):
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
    "novedad": {"titulo_portada": "LO NUEVO\nDE POWER BI",
                "ideas": [{"titulo": "Copilot", "texto": "Genera medidas DAX en lenguaje natural."}],
                "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT},
    "comparativa": {"titulo_portada": "EXCEL VS\nPYTHON",
                    "ideas": [{"titulo": "Excel", "texto": "Rápido para algo puntual."},
                              {"titulo": "Python", "texto": "Reproducible para algo repetido."}],
                    "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT},
    "rol": {"titulo_portada": "DATA\nANALYST",
            "ideas": [{"titulo": "Skills", "texto": "SQL, BI, comunicación."}],
            "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT},
    "tip": {"titulo_portada": "TOP N\nEN SQL",
            "ideas": [{"titulo": "Cómo", "texto": "ROW_NUMBER con PARTITION BY."}],
            "codigo": "SELECT 1;", "lenguaje": "sql",
            "caption": "c" * 500, "hashtags": HASHTAGS_DEFAULT},
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Genera el lote semanal de Data Snake")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    cfg = get_config()
    hoy = date.today()
    lote_semana = cfg.dir_salida / f"semana-{hoy:%Y-%m-%d}"

    if args.dry_run:
        piezas = [{"tipo": t, "item": {"id": "dry"}} for t in TIPOS]
        redacciones = [DRY_RUN[p["tipo"]] for p in piezas]
        novedad = None
    else:
        anio, semana, _ = hoy.isocalendar()
        seed = anio * 100 + semana
        novedad = feeds.elegir_novedad(cfg)
        piezas = plan_semana(cfg, seed, novedad)
        redacciones = []
        for p in piezas:
            redacciones.append(redactar_pieza(p["tipo"], p["item"], cfg))
            time.sleep(cfg.pausa_entre_llamadas)

    fallidas = 0
    with Renderer(cfg) as renderer:
        for i, (pieza, red) in enumerate(zip(piezas, redacciones), start=1):
            try:
                carpeta = armar_pieza(i, pieza["tipo"], pieza["item"], red, cfg, renderer, lote_semana)
                log.info("Pieza %02d lista: %s", i, carpeta.name)
            except Exception as e:  # noqa: BLE001
                fallidas += 1
                log.error("Pieza %02d (%s) falló: %s", i, pieza["tipo"], e)

    if lote_semana.exists():
        exportar.exportar(lote_semana, cfg.dir_salida / "ParaSubir" / lote_semana.name)

    if not args.dry_run:
        if novedad:
            feeds.registrar_vista(cfg, novedad["id"])
        for tipo, (banco, _) in TIPOS.items():
            if banco:
                ids = [p["item"]["id"] for p in piezas if p["tipo"] == tipo]
                registrar_usados(cfg, banco, ids)

    log.info("Lote %s: %d piezas, %d fallidas", lote_semana.name, len(piezas), fallidas)
    return 0 if fallidas < len(piezas) else 1


if __name__ == "__main__":
    sys.exit(main())
