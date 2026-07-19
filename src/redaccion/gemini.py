"""Cliente mínimo de la API de Gemini (REST, sin SDK). Copiado de Efecto Gambeta.

Free tier: https://aistudio.google.com → API key → secret GEMINI_API_KEY.
Pedimos respuesta JSON (response_mime_type) y validamos acá; si el modelo
devuelve algo roto, se reintenta.

Resistencia a 429 (sin cupo): la espera entre reintentos respeta el
Retry-After que manda la API (o crece de a 20 s), y si un modelo agota su
cupo se prueba con los modelos de respaldo antes de rendirse (2026-06-04:
una corrida cayó al plan B por un 429 con reintentos de 2 s).

Anti-cascada (2026-06-11): cuando la cuota DIARIA se agota, todos los modelos
dan 429 y no se recupera en lo que resta de la corrida. Antes cada pieza
disparaba hasta ~18 llamadas (3 intentos × 3 modelos × 2 intentos de
redacción) con esperas de 20-40 s: una corrida se colgaba horas. Ahora, en
cuanto los tres modelos dan 429, se prende un latch de proceso (_cupo_agotado)
y el resto de las piezas salen al toque por plan B, sin tocar la red.
"""

import json
import logging
import time

import requests

log = logging.getLogger("sosiego.gemini")

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# 2026-07-18: las keys nuevas ya no pueden usar los alias pinneados viejos
# (gemini-2.5-flash → 404 "no longer available to new users"; gemini-2.0-flash* → 429
# con cupo cero). Usamos los alias rolling "-latest", que Google mantiene apuntando
# siempre a un modelo vigente y no se deprecan bajo una key nueva.
MODEL_DEFAULT = "gemini-flash-latest"
# Si el modelo principal está sin cupo (429 persistente), se prueban estos en orden.
MODELOS_RESPALDO = ["gemini-flash-lite-latest", "gemini-3-flash-preview"]


class GeminiError(Exception):
    pass


class GeminiSinCupo(GeminiError):
    """429: cupo/tasa agotada. Si pasa en todos los modelos, prende el latch."""


# Latch de proceso: lo prende generar_json al ver 429 en TODOS los modelos.
# A partir de ahí, el resto de la corrida sale por plan B sin tocar la red.
_cupo_agotado = False


def _espera_para(respuesta: requests.Response | None, intento: int) -> float:
    """Cuánto esperar antes de reintentar: Retry-After si vino, si no 20s, 40s..."""
    if respuesta is not None:
        retry_after = respuesta.headers.get("Retry-After", "")
        if retry_after.isdigit():
            return min(int(retry_after), 90)
    return 20.0 * intento


def _llamar(prompt: str, api_key: str, model: str, reintentos: int) -> dict:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.8,
        },
    }

    ultimo_error: Exception | None = None
    es_429 = False
    for intento in range(1, reintentos + 1):
        respuesta = None
        try:
            respuesta = requests.post(
                URL.format(model=model),
                params={"key": api_key},
                json=body,
                timeout=90,
            )
            respuesta.raise_for_status()
            texto = respuesta.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(texto)
        except Exception as e:  # noqa: BLE001 — reintentamos cualquier fallo (HTTP o JSON roto)
            ultimo_error = e
            es_429 = respuesta is not None and respuesta.status_code == 429
            log.warning("Gemini (%s) intento %d/%d falló: %s", model, intento, reintentos, e)
            # 429 = cupo/tasa: un solo reintento corto (por si es RPM) y se abandona
            # este modelo; no tiene sentido agotar los 3 intentos con esperas largas.
            if es_429 and intento >= 2:
                break
            if intento < reintentos:
                time.sleep(_espera_para(respuesta, intento))

    if es_429:
        raise GeminiSinCupo(f"Gemini ({model}) sin cupo (429) tras {intento} intentos")
    raise GeminiError(f"Gemini ({model}) falló tras {reintentos} intentos: {ultimo_error}")


def generar_json(prompt: str, api_key: str, model: str = MODEL_DEFAULT, reintentos: int = 3) -> dict:
    """Manda el prompt y devuelve la respuesta parseada como dict.

    Prueba el modelo pedido y, si falla, los de respaldo. Lanza GeminiError
    si no hay key o si todos los modelos fallan.
    """
    global _cupo_agotado
    if not api_key:
        raise GeminiError("Falta GEMINI_API_KEY (ver GUIA-MANUAL.md)")
    if _cupo_agotado:
        raise GeminiSinCupo("Cupo de Gemini agotado en esta corrida: directo a plan B")

    modelos = [model] + [m for m in MODELOS_RESPALDO if m != model]
    ultimo_error: Exception | None = None
    todos_sin_cupo = True  # se baja si algún modelo falla por algo que no sea 429
    for m in modelos:
        try:
            return _llamar(prompt, api_key, m, reintentos)
        except GeminiSinCupo as e:
            ultimo_error = e
        except GeminiError as e:
            ultimo_error = e
            todos_sin_cupo = False

    if todos_sin_cupo:
        _cupo_agotado = True
        log.warning("Todos los modelos sin cupo (429): el resto de la corrida sale por plan B")
    raise GeminiError(f"Todos los modelos fallaron; último error: {ultimo_error}")
