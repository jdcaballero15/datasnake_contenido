"""Fuente viva: novedades de herramientas vía RSS/Atom (feedparser).

RSS-first: leemos feeds oficiales estables y elegimos la entrada más fresca
que no hayamos usado. Si una web no tiene feed, se puede sumar un scraper HTML
puntual acá; si algo falla, esa fuente rinde vacío y la corrida no se cae
(main.py cae a evergreen). Dedup en estado/fuente_vista.json.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

from src.config import FRESCURA_DIAS, Config


def cargar_feeds(cfg: Config) -> list[dict]:
    ruta = cfg.dir_datos / "feeds.json"
    if not ruta.exists():
        return []
    return json.loads(ruta.read_text(encoding="utf-8-sig"))


def _ruta_vistas(cfg: Config) -> Path:
    return cfg.dir_estado / "fuente_vista.json"


def cargar_vistas(cfg: Config) -> list[str]:
    ruta = _ruta_vistas(cfg)
    return json.loads(ruta.read_text(encoding="utf-8-sig")) if ruta.exists() else []


def registrar_vista(cfg: Config, entry_id: str) -> None:
    vistas = cargar_vistas(cfg)
    if entry_id not in vistas:
        vistas.append(entry_id)
    _ruta_vistas(cfg).parent.mkdir(parents=True, exist_ok=True)
    _ruta_vistas(cfg).write_text(
        json.dumps(vistas, ensure_ascii=False, indent=1), encoding="utf-8")


def _fecha(entry) -> datetime | None:
    st = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not st:
        return None
    return datetime.fromtimestamp(time.mktime(st), tz=timezone.utc)


def elegir_novedad(cfg: Config, ahora: datetime | None = None, parse=feedparser.parse) -> dict | None:
    """La novedad más fresca (dentro de FRESCURA_DIAS) que no se haya usado."""
    ahora = ahora or datetime.now(timezone.utc)
    limite = ahora - timedelta(days=FRESCURA_DIAS)
    vistas = set(cargar_vistas(cfg))
    candidatas: list[tuple[datetime, dict]] = []
    for feed in cargar_feeds(cfg):
        try:
            parsed = parse(feed["url"])
        except Exception:  # noqa: BLE001 — un feed roto no voltea la corrida
            continue
        for e in getattr(parsed, "entries", []):
            eid = getattr(e, "id", None) or getattr(e, "link", None)
            fecha = _fecha(e)
            if not eid or eid in vistas or fecha is None or fecha < limite:
                continue
            candidatas.append((fecha, {
                "id": eid,
                "titulo": getattr(e, "title", "").strip(),
                "resumen": getattr(e, "summary", "").strip(),
                "link": getattr(e, "link", ""),
                "fuente": feed["nombre"],
            }))
    if not candidatas:
        return None
    candidatas.sort(key=lambda c: c[0], reverse=True)
    return candidatas[0][1]
