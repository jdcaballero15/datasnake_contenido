"""Bancos JSON locales: la fuente evergreen de Data Snake.

Comparativas, roles y tips no caducan, así que viven en datos/*.json y Gemini
los desarrolla directo desde ahí; lo que sí es actualidad (novedades del mundo
data/tech) sale de RSS vía feeds.py. La selección es reproducible por seed
(relanzar la corrida la misma semana no duplica) y estado/usados.json evita
repetir contenido entre semanas.
"""

import json
import random
from pathlib import Path

from src.config import Config


def cargar_banco(cfg: Config, nombre: str) -> list[dict]:
    return json.loads((cfg.dir_datos / f"{nombre}.json").read_text(encoding="utf-8-sig"))


def _ruta_usados(cfg: Config) -> Path:
    return cfg.dir_estado / "usados.json"


def cargar_usados(cfg: Config) -> dict:
    """{banco: [ids ya publicados]}. Si no existe el archivo, nada se usó."""
    ruta = _ruta_usados(cfg)
    return json.loads(ruta.read_text(encoding="utf-8-sig")) if ruta.exists() else {}


def _guardar_usados(cfg: Config, usados: dict) -> None:
    ruta = _ruta_usados(cfg)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(usados, ensure_ascii=False, indent=1), encoding="utf-8")


def registrar_usados(cfg: Config, banco: str, ids: list[str]) -> None:
    usados = cargar_usados(cfg)
    usados[banco] = sorted(set(usados.get(banco, [])) | set(ids))
    _guardar_usados(cfg, usados)


def seleccionar(cfg: Config, banco: str, cantidad: int, seed: int) -> list[dict]:
    """Elige `cantidad` items aún no usados del banco.

    Si quedan menos libres que los pedidos, el banco se considera agotado:
    se resetea la rotación y se vuelve a elegir entre todos.
    """
    items = cargar_banco(cfg, banco)
    usados = set(cargar_usados(cfg).get(banco, []))
    libres = [i for i in items if i["id"] not in usados]
    if len(libres) < cantidad:
        usados_todos = cargar_usados(cfg)
        usados_todos[banco] = []
        _guardar_usados(cfg, usados_todos)
        libres = items
    return random.Random(seed).sample(libres, min(cantidad, len(libres)))
