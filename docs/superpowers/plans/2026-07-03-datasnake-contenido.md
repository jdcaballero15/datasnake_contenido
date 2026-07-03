# Data Snake Contenido — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a $0 automated content factory for Data Snake (data/tech niche): weekly it pulls tool novedades via RSS + evergreen banks, writes copy with Gemini, renders dark-theme carousels to PNG, optionally builds slideshow reels, and drops everything in Google Drive to post by hand.

**Architecture:** Reuse the *generation half* of the proven Efecto Sosiego repo (Gemini client, Playwright renderer, bank rotation, orchestrator skeleton, Drive delivery). Drop the entire publisher/Meta half and the comment responder. Add a new RSS source module and new dark-theme templates. Publication is 100% manual.

**Tech Stack:** Python 3.12 · `requests` `feedparser` `jinja2` `playwright` `pytest` · ffmpeg + rclone (CLI, in workflow) · GitHub Actions (cron) · Google Drive (rclone).

## Global Constraints

- **Reference repo (REF):** `/home/juan-diego/Documentos/efectososiego_contenido-master` — source of modules copied verbatim or adapted. Read a REF file before copying it.
- **Project root (ROOT):** `/home/juan-diego/data.snake/proyectos/datasnake_contenido` — already a git repo with the spec committed.
- **Python:** 3.12. All source under `src/`, run as modules (`python -m src.main`).
- **Budget $0:** no paid services, no database. Durable state lives in `estado/*.json` committed to the repo.
- **Brand palette (exact):** `COLOR_FONDO="#111827"`, `COLOR_TEXTO="#CBD5E1"`, `COLOR_ACENTO="#2A7FA8"`, `COLOR_BORDE="#253347"`, surface `#1C2B3A`, texto-sec `#7B91A8`, gradient `#7C5CBF`→`#2EE6A6`.
- **Handle:** `data.snake`. **Eslogan:** `Herramientas, resultados y carrera en data`.
- **Voice:** voseo, cercano y amigable, técnico, orientado a resultados; nunca inventar benchmarks/estudios/estadísticas.
- **Placa size:** 1080×1350 PNG. **Piece types:** `novedad` (RSS), `comparativa`/`rol`/`tip` (evergreen). Weekly mix: 1 novedad + 2 evergreen (rotating); novedad falls back to evergreen when no fresh item.
- **No network in tests.** Gemini and feeds are mocked/fixtured. `python -m src.main --dry-run` runs the whole pipeline offline.
- **Commit after every task** with a `feat:`/`chore:`/`test:` message.

## File Structure

```
ROOT/
├── requirements.txt                 deps (adds feedparser)
├── pytest.ini                       testpaths=tests
├── README.md                        short overview
├── MANUAL-TECNICO.md                living manual (knobs table)
├── marca/logos/logo.png             Data Snake icon on dark bg (from user's folder)
├── musica/                          CC0 mp3s (optional, for reels)
├── datos/
│   ├── comparativas.json            evergreen bank
│   ├── roles.json                   evergreen bank
│   ├── tips.json                    evergreen bank (with code snippets)
│   └── feeds.json                   list of RSS feeds for novedades
├── estado/
│   ├── usados.json                  {banco: [ids]} — evergreen rotation
│   └── fuente_vista.json            [entry ids] — novedades dedup
├── plantillas/
│   ├── _estilos.html                shared dark CSS + fonts + brand gradient
│   ├── portada.html                 carousel cover
│   ├── idea.html                    numbered idea/step card
│   ├── codigo.html                  code snippet card (syntax colors via CSS)
│   ├── comparativa.html             "vs" comparison card
│   └── cierre.html                  closing card: CTA + @data.snake + eslogan
├── src/
│   ├── config.py                    ⭐ all knobs (adapted)
│   ├── fuentes/
│   │   ├── bancos.py                bank selection+rotation (copied, trimmed)
│   │   └── feeds.py                 ⭐ RSS-first novedades (new)
│   ├── redaccion/
│   │   ├── gemini.py                Gemini client (copied verbatim)
│   │   ├── prompts.py               ⭐ Data Snake voice + JSON contracts (new)
│   │   └── contratos.py             response validation (adapted)
│   ├── render/renderer.py           HTML→PNG (copied verbatim)
│   ├── video/reel_slideshow.py      placas→mp4 slideshow (new, optional)
│   ├── audio/musica.py              pick CC0 track (copied verbatim)
│   ├── exportar.py                  flat "ParaSubir/" + 00-CAPTIONS.txt (adapted)
│   └── main.py                      ⭐ orchestrator (adapted)
├── tests/…                          pytest mirror
└── .github/workflows/contenido.yml  cron + run + Drive delivery (adapted)
```

---

### Task 1: Scaffold, config, and logo asset

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `src/__init__.py`, `src/config.py`, `marca/logos/logo.png`
- Create: `src/fuentes/__init__.py`, `src/redaccion/__init__.py`, `src/render/__init__.py`, `src/video/__init__.py`, `src/audio/__init__.py`
- Test: `tests/__init__.py`, `tests/test_config.py`

**Interfaces:**
- Produces: `get_config() -> Config` with attrs `gemini_api_key, dir_datos, dir_estado, dir_salida, dir_plantillas, ruta_logo, ig_handle, mix, tipos_evergreen, pausa_entre_llamadas, segundos_por_slide`. Module constants: `COLOR_FONDO, COLOR_TEXTO, COLOR_ACENTO, COLOR_BORDE, COLOR_SURFACE, COLOR_TEXTO_SEC, GRAD_A, GRAD_B, ESLOGAN, CTA_COMPARTIR, CTA_GUARDAR, HASHTAGS_DEFAULT, MIX_NOVEDAD, TIPOS_EVERGREEN, FRESCURA_DIAS`.

- [ ] **Step 1: Copy the logo asset**

```bash
mkdir -p /home/juan-diego/data.snake/proyectos/datasnake_contenido/marca/logos
cp "/home/juan-diego/data.snake/WhatsApp Image 2026-06-24 at 18.46.17.jpeg" \
   /home/juan-diego/data.snake/proyectos/datasnake_contenido/marca/logos/logo.png
```
(That JPEG is the icon-only snake on the dark background — the best fit for embedding. `.png` extension is fine; the renderer sniffs mime by content type via `mimetypes`, and the file is embedded as a data-URI regardless.)

- [ ] **Step 2: Write `requirements.txt` and `pytest.ini`**

`requirements.txt`:
```
requests==2.32.5
feedparser==6.0.11
jinja2==3.1.6
playwright==1.55.0
pytest==8.4.2
```
`pytest.ini`:
```
[pytest]
testpaths = tests
```

- [ ] **Step 3: Create empty package inits**

Create these as empty files: `src/__init__.py`, `src/fuentes/__init__.py`, `src/redaccion/__init__.py`, `src/render/__init__.py`, `src/video/__init__.py`, `src/audio/__init__.py`, `tests/__init__.py`.

- [ ] **Step 4: Write the failing test** — `tests/test_config.py`

```python
from src import config
from src.config import get_config


def test_palette_is_data_snake_dark():
    assert config.COLOR_FONDO == "#111827"
    assert config.COLOR_TEXTO == "#CBD5E1"
    assert config.COLOR_ACENTO == "#2A7FA8"
    assert config.COLOR_BORDE == "#253347"


def test_brand_strings():
    assert config.ESLOGAN == "Herramientas, resultados y carrera en data"
    assert get_config().ig_handle == "data.snake"


def test_mix_is_one_novedad_two_evergreen():
    cfg = get_config()
    assert config.MIX_NOVEDAD == 1
    assert set(config.TIPOS_EVERGREEN) == {"comparativa", "rol", "tip"}
    assert cfg.mix["evergreen"] == 2


def test_hashtags_capped_at_five():
    assert len(config.HASHTAGS_DEFAULT) <= 5
```

- [ ] **Step 5: Run test to verify it fails**

Run: `cd ROOT && python -m pytest tests/test_config.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.config'`).

- [ ] **Step 6: Write `src/config.py`**

```python
"""Configuración de Data Snake. TODO lo ajustable vive acá."""

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_MUSICA = RAIZ / "musica"

# Paleta de marca (dark). Base azul-forward; gradiente violeta→verde para acentos.
COLOR_FONDO = "#111827"        # Midnight
COLOR_TEXTO = "#CBD5E1"        # Cloud
COLOR_ACENTO = "#2A7FA8"       # Ocean Blue
COLOR_BORDE = "#253347"        # Border
COLOR_SURFACE = "#1C2B3A"      # Deep Slate (cards)
COLOR_TEXTO_SEC = "#7B91A8"    # Mist
GRAD_A = "#7C5CBF"             # Slate Violet
GRAD_B = "#2EE6A6"             # verde del logo

# Mix semanal: 1 novedad (RSS) + 2 evergreen rotando entre estos tipos.
MIX_NOVEDAD = 1
TIPOS_EVERGREEN = ["comparativa", "rol", "tip"]

# Ventana de frescura de las novedades (la corrida es semanal).
FRESCURA_DIAS = 14

ESLOGAN = "Herramientas, resultados y carrera en data"

# Doble CTA fija del caption (señales del algoritmo: compartir + guardar), tono tech.
CTA_COMPARTIR = "📩 Mandáselo a alguien que esté metido en data."
CTA_GUARDAR = "🔖 Guardalo para tu próximo proyecto."

HASHTAGS_DEFAULT = ["data", "analytics", "powerbi", "sql", "python"]

# Reels de slideshow (opcional): segundos por placa.
SEGUNDOS_POR_SLIDE = 3


@dataclass
class Config:
    gemini_api_key: str = ""
    dir_datos: Path = RAIZ / "datos"
    dir_estado: Path = RAIZ / "estado"
    dir_salida: Path = RAIZ / "salida"
    dir_plantillas: Path = RAIZ / "plantillas"
    ruta_logo: Path = RAIZ / "marca" / "logos" / "logo.png"
    ig_handle: str = "data.snake"
    mix: dict = field(default_factory=lambda: {"novedad": MIX_NOVEDAD, "evergreen": 2})
    tipos_evergreen: list = field(default_factory=lambda: list(TIPOS_EVERGREEN))
    segundos_por_slide: int = SEGUNDOS_POR_SLIDE
    pausa_entre_llamadas: float = 7.0  # anti rate-limit del free tier de Gemini


def get_config() -> Config:
    return Config(gemini_api_key=os.environ.get("GEMINI_API_KEY", ""))
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd ROOT && python -m pytest tests/test_config.py -v`
Expected: PASS (4 tests).

- [ ] **Step 8: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: scaffold project, config, logo asset"
```

---

### Task 2: Evergreen banks + bank selection

**Files:**
- Create: `src/fuentes/bancos.py`, `datos/comparativas.json`, `datos/roles.json`, `datos/tips.json`
- Test: `tests/test_bancos.py`

**Interfaces:**
- Consumes: `Config` (Task 1).
- Produces: `cargar_banco(cfg, nombre) -> list[dict]`; `seleccionar(cfg, banco, cantidad, seed) -> list[dict]`; `cargar_usados(cfg) -> dict`; `registrar_usados(cfg, banco, ids) -> None`.

- [ ] **Step 1: Copy and trim `bancos.py` from REF**

Read `REF/src/fuentes/bancos.py`, then create `ROOT/src/fuentes/bancos.py` as a copy **without** `seleccionar_ejercicios` (mindfulness-only). Keep `cargar_banco`, `_ruta_usados`, `cargar_usados`, `_guardar_usados`, `registrar_usados`, `seleccionar` exactly as in REF. Update the module docstring to say the banks are the evergreen source for Data Snake and novedades come from `feeds.py`.

- [ ] **Step 2: Write the evergreen banks (start with ~15 items each; here are seed items)**

`datos/comparativas.json`:
```json
[
  {"id": "c01", "tarea": "Limpiar 10.000 filas con nulos y duplicados",
   "opciones": ["Excel: filtros + quitar duplicados, ~8 pasos manuales",
                "Python/pandas: dropna + drop_duplicates, 3 líneas reproducibles",
                "SQL: WHERE + DISTINCT en la consulta, corre en el server"],
   "veredicto": "Para algo puntual, Excel; para algo repetible, pandas o SQL."},
  {"id": "c02", "tarea": "Un dashboard que se actualice solo",
   "opciones": ["Power BI: refresh programado + publish al Service",
                "Tableau: extract refresh o live connection",
                "Excel: Power Query + refrescar a mano o con macro"],
   "veredicto": "Power BI/Tableau para producción; Excel solo si el equipo ya lo usa."}
]
```

`datos/roles.json`:
```json
[
  {"id": "r01", "rol": "Data Analyst",
   "skills": ["SQL sólido", "una herramienta de BI (Power BI o Tableau)", "algo de Python/Excel avanzado", "comunicar hallazgos"],
   "herramientas": ["SQL", "Power BI", "Excel", "Python"],
   "gancho": "El puente entre los datos crudos y la decisión de negocio."},
  {"id": "r02", "rol": "Analytics Engineer",
   "skills": ["SQL avanzado", "dbt", "modelado de datos", "control de versiones (git)"],
   "herramientas": ["dbt", "SQL", "Snowflake/BigQuery", "git"],
   "gancho": "Deja la data lista y confiable para que otros la usen."}
]
```

`datos/tips.json`:
```json
[
  {"id": "t01", "titulo": "Rankear sin subconsultas en SQL",
   "lenguaje": "sql", "gancho": "Top N por grupo en una sola pasada",
   "codigo": "SELECT *\nFROM (\n  SELECT *,\n    ROW_NUMBER() OVER (\n      PARTITION BY categoria ORDER BY ventas DESC) AS rn\n  FROM ventas\n) t\nWHERE rn <= 3;",
   "explicacion": "ROW_NUMBER() con PARTITION BY numera dentro de cada grupo; filtrás rn<=3 y tenés el top 3 por categoría."},
  {"id": "t02", "titulo": "Medida de crecimiento en DAX",
   "lenguaje": "dax", "gancho": "Variación % vs. período anterior sin romperte la cabeza",
   "codigo": "Crecimiento % =\nVAR Actual = SUM(Ventas[Monto])\nVAR Previo = CALCULATE(SUM(Ventas[Monto]),\n    DATEADD(Calendario[Fecha], -1, MONTH))\nRETURN DIVIDE(Actual - Previo, Previo)",
   "explicacion": "DATEADD mueve el contexto un mes atrás; DIVIDE evita el error de división por cero."}
]
```
(Add more items to reach ~15 per bank following the same shapes. Every item needs a unique `id`.)

- [ ] **Step 3: Write the failing test** — `tests/test_bancos.py`

```python
import json

from src.config import get_config
from src.fuentes import bancos


def test_banks_load_and_have_unique_ids(tmp_path):
    cfg = get_config()
    for nombre in ("comparativas", "roles", "tips"):
        items = bancos.cargar_banco(cfg, nombre)
        ids = [i["id"] for i in items]
        assert len(ids) == len(set(ids)), f"{nombre} has duplicate ids"
        assert len(items) >= 2


def test_seleccionar_is_deterministic_by_seed(tmp_path, monkeypatch):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    a = bancos.seleccionar(cfg, "roles", 1, seed=202627)
    b = bancos.seleccionar(cfg, "roles", 1, seed=202627)
    assert a == b


def test_registrar_usados_persists(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    bancos.registrar_usados(cfg, "roles", ["r01"])
    assert bancos.cargar_usados(cfg)["roles"] == ["r01"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ROOT && python -m pytest tests/test_bancos.py -v`
Expected: PASS (3 tests). If FAIL on load, check the JSON is valid (`python -m json.tool datos/roles.json`).

- [ ] **Step 5: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: evergreen banks + bank selection/rotation"
```

---

### Task 3: RSS novedades source (`feeds.py`)

**Files:**
- Create: `src/fuentes/feeds.py`, `datos/feeds.json`
- Test: `tests/test_feeds.py`, `tests/fixtures/feed_ejemplo.xml`

**Interfaces:**
- Consumes: `Config`; `FRESCURA_DIAS` from config.
- Produces:
  - `cargar_feeds(cfg) -> list[dict]` — reads `datos/feeds.json` (`[{"nombre","url"}]`).
  - `cargar_vistas(cfg) -> list[str]`; `registrar_vista(cfg, entry_id) -> None` (writes `estado/fuente_vista.json`).
  - `elegir_novedad(cfg, ahora=None, parse=feedparser.parse) -> dict | None` — returns the freshest unseen entry within `FRESCURA_DIAS` as `{"id","titulo","resumen","link","fuente"}`, or `None`. `parse` is injectable for tests.

- [ ] **Step 1: Write `datos/feeds.json` (starter list — official blogs with feeds)**

```json
[
  {"nombre": "Power BI", "url": "https://powerbi.microsoft.com/en-us/blog/feed/"},
  {"nombre": "AWS Big Data", "url": "https://aws.amazon.com/blogs/big-data/feed/"},
  {"nombre": "Tableau", "url": "https://www.tableau.com/blog/feed"},
  {"nombre": "Anthropic News", "url": "https://www.anthropic.com/news/rss.xml"}
]
```
(URLs are best-effort; confirm each returns a feed during first real run. A dead feed just yields no entries — it never breaks the run.)

- [ ] **Step 2: Write the test fixture** — `tests/fixtures/feed_ejemplo.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Power BI Blog</title>
  <item>
    <title>Nueva función de copilot en Power BI</title>
    <link>https://example.com/nuevo-copilot</link>
    <guid>https://example.com/nuevo-copilot</guid>
    <description>Ahora podés generar medidas DAX describiéndolas en lenguaje natural.</description>
    <pubDate>__RECIENTE__</pubDate>
  </item>
  <item>
    <title>Novedad vieja</title>
    <link>https://example.com/vieja</link>
    <guid>https://example.com/vieja</guid>
    <description>Algo de hace un año.</description>
    <pubDate>Mon, 01 Jul 2024 10:00:00 GMT</pubDate>
  </item>
</channel></rss>
```

- [ ] **Step 3: Write the failing test** — `tests/test_feeds.py`

```python
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import feedparser

from src.config import get_config
from src.fuentes import feeds

FIXTURE = Path(__file__).parent / "fixtures" / "feed_ejemplo.xml"


def _parse_fixture_reciente(_url):
    reciente = format_datetime(datetime.now(timezone.utc))
    xml = FIXTURE.read_text(encoding="utf-8").replace("__RECIENTE__", reciente)
    return feedparser.parse(xml)


def test_elige_la_entrada_fresca_no_la_vieja(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text('[{"nombre":"PBI","url":"x"}]', encoding="utf-8")
    nov = feeds.elegir_novedad(cfg, parse=_parse_fixture_reciente)
    assert nov is not None
    assert nov["titulo"] == "Nueva función de copilot en Power BI"
    assert nov["fuente"] == "PBI"


def test_no_repite_novedad_ya_vista(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text('[{"nombre":"PBI","url":"x"}]', encoding="utf-8")
    feeds.registrar_vista(cfg, "https://example.com/nuevo-copilot")
    nov = feeds.elegir_novedad(cfg, parse=_parse_fixture_reciente)
    assert nov is None  # la fresca ya fue vista, la otra está fuera de la ventana


def test_sin_feeds_devuelve_none(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.dir_datos = tmp_path
    (tmp_path / "feeds.json").write_text("[]", encoding="utf-8")
    assert feeds.elegir_novedad(cfg, parse=_parse_fixture_reciente) is None
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd ROOT && python -m pytest tests/test_feeds.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.fuentes.feeds'`).

- [ ] **Step 5: Write `src/fuentes/feeds.py`**

```python
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd ROOT && python -m pytest tests/test_feeds.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: RSS-first novedades source with freshness + dedup"
```

---

### Task 4: Gemini client, prompts, and contracts

**Files:**
- Create: `src/redaccion/gemini.py` (copied verbatim), `src/redaccion/prompts.py` (new), `src/redaccion/contratos.py` (adapted)
- Test: `tests/test_prompts.py`, `tests/test_contratos.py`

**Interfaces:**
- Consumes: nothing new.
- Produces:
  - `gemini.generar_json(prompt, api_key) -> dict` and `gemini.GeminiError` (unchanged from REF).
  - `prompts.prompt_novedad(item)`, `prompt_comparativa(item)`, `prompt_rol(item)`, `prompt_tip(item)` → `str`.
  - `contratos.validar(tipo, datos) -> None` (raises `ValueError` on bad shape).

- [ ] **Step 1: Copy `gemini.py` verbatim**

Read `REF/src/redaccion/gemini.py`, then create `ROOT/src/redaccion/gemini.py` with identical content (Gemini REST client, `MODEL_DEFAULT`/`MODELOS_RESPALDO`, 429 retries + `_cupo_agotado` latch). No changes.

- [ ] **Step 2: Write `src/redaccion/prompts.py`**

```python
"""Prompts para Gemini: voz de marca Data Snake + contrato JSON por tipo.

Para cambiar el tono de la cuenta, este archivo es EL lugar (junto con config.py).
"""

VOZ_DE_MARCA = """\
Sos la voz de "Data Snake", una cuenta sobre analítica de datos, herramientas y
carreras en el mundo data. Hablás en español rioplatense (voseo), cercano y
amigable, pero técnico y al grano: mostrás lo que la herramienta HACE y LOGRA,
con foco en resultados. Tu público YA está en tech (analistas, gente de datos),
así que no explicás lo obvio ni decís "esto es fácil, arrancá acá". Nunca
inventás benchmarks, estudios ni estadísticas: si no tenés un dato real, hablás
de la mecánica y el beneficio concreto, no de números inventados."""

REGLAS_CAPTION = """\
El "caption" es de retención: 6-10 oraciones (~600-900 caracteres) en 2-3
párrafos separados por \\n. Abrí con el problema o el resultado, desarrollá con
tu mirada técnica y cerrá con el para-qué. SIN llamados a la acción (los
agregamos nosotros). "hashtags": 4 a 5, sin #, en minúsculas, del mundo
data/tech (ej. data, sql, powerbi, python, analytics)."""

_CIERRE = """Responde SOLO con un JSON válido, exactamente con esta forma:"""


def prompt_novedad(item: dict) -> str:
    return f"""{VOZ_DE_MARCA}

Material — novedad de la herramienta (fuente: {item['fuente']}):
Título: "{item['titulo']}"
Resumen: {item['resumen']}

TAREA — Convertí la novedad en un carrusel: una portada con el título en corto y
3 a 5 ideas concretas de QUÉ salió y QUÉ te permite hacer ahora en tu trabajo.
No exageres ni prometas lo que no dice el material.

{REGLAS_CAPTION}

{_CIERRE}
{{
  "titulo_portada": "<MAYÚSCULAS, máximo 3 líneas de 1-3 palabras, con \\n>",
  "ideas": [{{"titulo": "<título corto>", "texto": "<1-3 oraciones>"}}],
  "caption": "<6-10 oraciones, ~600-900 caracteres>",
  "hashtags": ["<4 a 5>"]
}}"""


def prompt_comparativa(item: dict) -> str:
    opciones = "\n".join(f"- {o}" for o in item["opciones"])
    return f"""{VOZ_DE_MARCA}

Material — comparativa para la tarea: "{item['tarea']}".
Opciones:
{opciones}
Veredicto sugerido: {item['veredicto']}

TAREA — Armá un carrusel que enfrente las opciones para esa tarea: portada +
una idea por opción (cuándo conviene cada una) + una idea de cierre con el
veredicto. Concreto y honesto, sin fanatismos de herramienta.

{REGLAS_CAPTION}

{_CIERRE}
{{
  "titulo_portada": "<MAYÚSCULAS, máximo 3 líneas de 1-3 palabras, con \\n>",
  "ideas": [{{"titulo": "<opción o cierre>", "texto": "<1-3 oraciones>"}}],
  "caption": "<6-10 oraciones, ~600-900 caracteres>",
  "hashtags": ["<4 a 5>"]
}}"""


def prompt_rol(item: dict) -> str:
    skills = ", ".join(item["skills"])
    return f"""{VOZ_DE_MARCA}

Material — rol del mundo data: "{item['rol']}".
Gancho: {item['gancho']}
Skills: {skills}
Herramientas: {", ".join(item['herramientas'])}

TAREA — Armá un carrusel sobre el rol: portada + 3 a 5 ideas (qué hace, qué
skills/herramientas pide, cómo se llega). Realista y útil para alguien que
evalúa apuntar a ese rol.

{REGLAS_CAPTION}

{_CIERRE}
{{
  "titulo_portada": "<MAYÚSCULAS, máximo 3 líneas de 1-3 palabras, con \\n>",
  "ideas": [{{"titulo": "<título corto>", "texto": "<1-3 oraciones>"}}],
  "caption": "<6-10 oraciones, ~600-900 caracteres>",
  "hashtags": ["<4 a 5>"]
}}"""


def prompt_tip(item: dict) -> str:
    return f"""{VOZ_DE_MARCA}

Material — tip técnico: "{item['titulo']}" (lenguaje: {item['lenguaje']}).
Gancho: {item['gancho']}
Código:
{item['codigo']}
Explicación base: {item['explicacion']}

TAREA — Armá un carrusel con: portada, una placa con la EXPLICACIÓN del tip en
1-3 ideas, y devolvé el CÓDIGO tal cual para mostrarlo en una placa aparte. No
cambies el código salvo erratas evidentes.

{REGLAS_CAPTION}

{_CIERRE}
{{
  "titulo_portada": "<MAYÚSCULAS, máximo 3 líneas de 1-3 palabras, con \\n>",
  "ideas": [{{"titulo": "<título corto>", "texto": "<1-3 oraciones>"}}],
  "codigo": "<el código, con saltos de línea reales>",
  "lenguaje": "{item['lenguaje']}",
  "caption": "<6-10 oraciones, ~600-900 caracteres>",
  "hashtags": ["<4 a 5>"]
}}"""
```

- [ ] **Step 3: Write `src/redaccion/contratos.py`**

```python
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
```

- [ ] **Step 4: Write the failing tests** — `tests/test_prompts.py` and `tests/test_contratos.py`

`tests/test_prompts.py`:
```python
from src.redaccion import prompts


def test_voz_es_voseo():
    assert "voseo" in prompts.VOZ_DE_MARCA.lower() or "sos la voz" in prompts.VOZ_DE_MARCA.lower()


def test_prompt_tip_incluye_codigo_y_pide_json():
    item = {"titulo": "X", "lenguaje": "sql", "gancho": "g",
            "codigo": "SELECT 1;", "explicacion": "e"}
    p = prompts.prompt_tip(item)
    assert "SELECT 1;" in p
    assert '"codigo"' in p


def test_prompt_comparativa_lista_opciones():
    item = {"tarea": "t", "opciones": ["A", "B"], "veredicto": "v"}
    p = prompts.prompt_comparativa(item)
    assert "- A" in p and "- B" in p
```

`tests/test_contratos.py`:
```python
import pytest

from src.redaccion import contratos

BASE = {"titulo_portada": "HOLA", "ideas": [{"titulo": "t", "texto": "x"}],
        "caption": "c" * 500, "hashtags": ["data"]}


def test_valida_novedad_ok():
    contratos.validar("novedad", dict(BASE))


def test_rechaza_caption_corto():
    with pytest.raises(ValueError):
        contratos.validar("novedad", {**BASE, "caption": "corto"})


def test_tip_requiere_codigo():
    with pytest.raises(ValueError):
        contratos.validar("tip", dict(BASE))  # sin 'codigo'
    contratos.validar("tip", {**BASE, "codigo": "SELECT 1;"})
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ROOT && python -m pytest tests/test_prompts.py tests/test_contratos.py -v`
Expected: PASS (6 tests).

- [ ] **Step 6: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: gemini client + Data Snake prompts + contracts"
```

---

### Task 5: Dark-theme templates + renderer

**Files:**
- Create: `plantillas/_estilos.html`, `plantillas/portada.html`, `plantillas/idea.html`, `plantillas/codigo.html`, `plantillas/comparativa.html`, `plantillas/cierre.html`, `src/render/renderer.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: `Config`, brand constants.
- Produces: `Renderer(cfg)` context manager with `render_placa(contexto: dict, destino: Path) -> Path`. `contexto["plantilla"]` ∈ {portada, idea, codigo, comparativa, cierre}.

- [ ] **Step 1: Copy `renderer.py` from REF, adapting the brand import**

Read `REF/src/render/renderer.py`, then create `ROOT/src/render/renderer.py` identical **except** the injected context: keep `logo_uri`, `ig_handle`, `eslogan`, and also inject the palette so templates can use it. Replace the `render_placa` context defaults block with:

```python
        contexto = dict(contexto)
        contexto.setdefault("logo_uri", _como_data_uri(self.cfg.ruta_logo))
        contexto.setdefault("ig_handle", self.cfg.ig_handle)
        contexto.setdefault("eslogan", ESLOGAN)
        contexto.setdefault("c", {
            "fondo": COLOR_FONDO, "texto": COLOR_TEXTO, "acento": COLOR_ACENTO,
            "borde": COLOR_BORDE, "surface": COLOR_SURFACE, "texto_sec": COLOR_TEXTO_SEC,
            "grad_a": GRAD_A, "grad_b": GRAD_B,
        })
```
and update the import to:
```python
from src.config import (COLOR_ACENTO, COLOR_BORDE, COLOR_FONDO, COLOR_SURFACE,
                        COLOR_TEXTO, COLOR_TEXTO_SEC, ESLOGAN, GRAD_A, GRAD_B, Config)
```

- [ ] **Step 2: Write `plantillas/_estilos.html`**

```html
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:1080px; height:1350px; }
  body {
    background:{{ c.fondo }};
    color:{{ c.texto }};
    font-family:'Sora',system-ui,sans-serif;
    padding:96px 88px;
    display:flex; flex-direction:column;
    position:relative; overflow:hidden;
  }
  .grad { background:linear-gradient(120deg,{{ c.grad_a }},{{ c.grad_b }});
          -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  .tag { color:{{ c.texto_sec }}; font-size:34px; font-weight:600;
         letter-spacing:.12em; text-transform:uppercase; }
  .logo { height:64px; opacity:.95; }
  .pie { margin-top:auto; display:flex; align-items:center; gap:20px;
         color:{{ c.texto_sec }}; font-size:30px; }
  code, pre { font-family:'JetBrains Mono',monospace; }
</style>
```

- [ ] **Step 3: Write the four content templates**

`plantillas/portada.html`:
```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
  <div class="tag">{{ tag }}</div>
  <h1 class="grad" style="font-size:110px;font-weight:800;line-height:1.05;margin-top:40px;white-space:pre-line;">{{ titulo }}</h1>
  <div class="pie"><img class="logo" src="{{ logo_uri }}"> @{{ ig_handle }}</div>
</body></html>
```

`plantillas/idea.html`:
```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
  <div class="tag">{{ '%02d'|format(numero) }}</div>
  <h2 style="font-size:66px;font-weight:800;margin-top:28px;color:{{ c.texto }};">{{ titulo }}</h2>
  <p style="font-size:46px;line-height:1.4;margin-top:36px;color:{{ c.texto }};">{{ texto }}</p>
  <div class="pie"><span style="width:14px;height:14px;border-radius:50%;background:{{ c.acento }};"></span> @{{ ig_handle }}</div>
</body></html>
```

`plantillas/codigo.html`:
```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
  <div class="tag">{{ lenguaje|upper }}</div>
  <pre style="background:{{ c.surface }};border:2px solid {{ c.borde }};border-radius:24px;
              padding:44px;margin-top:36px;font-size:38px;line-height:1.5;color:{{ c.texto }};
              white-space:pre-wrap;word-break:break-word;">{{ codigo }}</pre>
  <div class="pie"><img class="logo" src="{{ logo_uri }}"> @{{ ig_handle }}</div>
</body></html>
```

`plantillas/comparativa.html`:
```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
  <div class="tag">{{ '%02d'|format(numero) }}</div>
  <h2 class="grad" style="font-size:64px;font-weight:800;margin-top:28px;">{{ titulo }}</h2>
  <p style="font-size:46px;line-height:1.4;margin-top:36px;color:{{ c.texto }};">{{ texto }}</p>
  <div class="pie"><span style="width:14px;height:14px;border-radius:50%;background:{{ c.grad_b }};"></span> @{{ ig_handle }}</div>
</body></html>
```

- [ ] **Step 4: Write `plantillas/cierre.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
  <img class="logo" style="height:120px;" src="{{ logo_uri }}">
  <h2 class="grad" style="font-size:72px;font-weight:800;margin-top:48px;">{{ eslogan }}</h2>
  <p style="font-size:44px;margin-top:36px;color:{{ c.texto_sec }};">Seguí a @{{ ig_handle }} por más.</p>
  <div class="pie">@{{ ig_handle }}</div>
</body></html>
```

- [ ] **Step 5: Ensure Playwright Chromium is installed (once)**

Run: `cd ROOT && python -m playwright install chromium`
Expected: downloads/updates Chromium (or reports already installed).

- [ ] **Step 6: Write the failing test** — `tests/test_render.py`

```python
from src.config import get_config
from src.render.renderer import Renderer

PLACAS = [
    {"plantilla": "portada", "tag": "Novedad", "titulo": "LO NUEVO\nDE POWER BI"},
    {"plantilla": "idea", "numero": 1, "titulo": "Copilot", "texto": "Genera DAX en lenguaje natural."},
    {"plantilla": "codigo", "lenguaje": "sql", "codigo": "SELECT 1;"},
    {"plantilla": "comparativa", "numero": 2, "titulo": "Excel vs Python", "texto": "Depende del volumen."},
    {"plantilla": "cierre"},
]


def test_render_cada_plantilla_produce_png(tmp_path):
    cfg = get_config()
    with Renderer(cfg) as r:
        for i, ctx in enumerate(PLACAS, start=1):
            destino = tmp_path / f"{i:02d}.png"
            r.render_placa(ctx, destino)
            assert destino.exists() and destino.stat().st_size > 1000
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd ROOT && python -m pytest tests/test_render.py -v`
Expected: PASS. (If it fails on fonts/network, the Google Fonts `@import` needs the runner online; the render still succeeds with fallback fonts, and the PNG is still produced — the assertion only checks a non-trivial file exists.)

- [ ] **Step 8: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: dark-theme templates + renderer"
```

---

### Task 6: Optional slideshow reel

**Files:**
- Create: `src/video/reel_slideshow.py`, `src/audio/musica.py` (copied verbatim)
- Test: `tests/test_reel_slideshow.py`

**Interfaces:**
- Consumes: `Config`, `DIR_MUSICA`.
- Produces: `generar_reel(carpeta: Path, cfg: Config, seed: int) -> Path | None` — builds `carpeta/reel.mp4` from the `NN.png` placas in `carpeta` (9:16, music if available). Returns the path, or `None` if ffmpeg or placas are missing.

- [ ] **Step 1: Copy `musica.py` verbatim**

Read `REF/src/audio/musica.py`, then create `ROOT/src/audio/musica.py` identical. (It picks a deterministic CC0 track from `musica/`; if the folder is empty it returns `None`, which the reel handles.)

- [ ] **Step 2: Write the failing test** — `tests/test_reel_slideshow.py`

```python
import shutil

import pytest

from src.config import get_config
from src.video import reel_slideshow


def test_sin_placas_devuelve_none(tmp_path):
    cfg = get_config()
    assert reel_slideshow.generar_reel(tmp_path, cfg, seed=1) is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg no instalado")
def test_con_placas_arma_mp4(tmp_path):
    cfg = get_config()
    # dos placas mínimas (PNG 1x1) para el slideshow
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d4944415478da6360000002000154a2b4bd0000000049454e44ae426082")
    (tmp_path / "01.png").write_bytes(png)
    (tmp_path / "02.png").write_bytes(png)
    salida = reel_slideshow.generar_reel(tmp_path, cfg, seed=1)
    assert salida is not None and salida.exists()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd ROOT && python -m pytest tests/test_reel_slideshow.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 4: Write `src/video/reel_slideshow.py`**

```python
"""Reel opcional: las placas del carrusel como slideshow 9:16 con música.

Enfoque liviano (estilo Efecto Gambeta): NO anima; encadena los PNG con
ffmpeg. Si falta ffmpeg o no hay placas, devuelve None y la pieza sale sin
reel (nunca voltea la corrida). Render atómico: escribe a reel.tmp.mp4 y
renombra solo si ffmpeg terminó bien.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from src.audio.musica import elegir_pista
from src.config import Config

log = logging.getLogger("datasnake.reel")


def generar_reel(carpeta: Path, cfg: Config, seed: int) -> Path | None:
    if shutil.which("ffmpeg") is None:
        log.warning("ffmpeg no disponible: la pieza sale sin reel")
        return None
    placas = sorted(carpeta.glob("[0-9][0-9].png"))
    if not placas:
        return None

    tmp = carpeta / "reel.tmp.mp4"
    destino = carpeta / "reel.mp4"
    seg = cfg.segundos_por_slide
    vf = ("scale=1080:1350:force_original_aspect_ratio=decrease,"
          "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x111827,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-framerate", f"1/{seg}",
           "-pattern_type", "glob", "-i", str(carpeta / "[0-9][0-9].png")]

    pista = elegir_pista(cfg, seed) if hasattr(__import__("src.audio.musica", fromlist=["elegir_pista"]), "elegir_pista") else None
    if pista:
        cmd += ["-i", str(pista), "-c:a", "aac", "-shortest"]
    cmd += ["-vf", vf, "-r", "30", "-c:v", "libx264", "-movflags", "+faststart", str(tmp)]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except (subprocess.CalledProcessError, OSError) as e:
        log.error("ffmpeg falló: %s", e)
        tmp.unlink(missing_ok=True)
        return None
    tmp.rename(destino)
    return destino
```
> Note: `musica.py`'s public function name may differ in REF (e.g. `elegir_pista` vs `elegir`). After copying it in Step 1, open it and set the import/call to the actual function name; if it takes different args, adapt the one call site above. If `musica.py` exposes nothing usable, drop the music lines — the reel works silently.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ROOT && python -m pytest tests/test_reel_slideshow.py -v`
Expected: PASS (2 tests, or 1 pass + 1 skip if ffmpeg absent locally).

- [ ] **Step 6: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: optional slideshow reel from placas"
```

---

### Task 7: Orchestrator + export

**Files:**
- Create: `src/main.py`, `src/exportar.py`
- Test: `tests/test_main.py`, `tests/test_exportar.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `plan_semana(cfg, seed, novedad) -> list[dict]` → list of `{"tipo","item"}`.
  - `construir_placas(tipo, red) -> list[dict]` → render contexts.
  - `armar_caption(cuerpo, hashtags) -> str`.
  - `main(argv=None) -> int`.
  - `exportar.exportar(lote_dir, destino) -> None` (flat `ParaSubir/` + `00-CAPTIONS.txt`).

- [ ] **Step 1: Write `src/exportar.py`**

```python
"""Carpeta plana ParaSubir/ + 00-CAPTIONS.txt para subir a mano de una."""

import shutil
from pathlib import Path


def exportar(lote_dir: Path, destino: Path) -> None:
    if not lote_dir.exists():
        return
    destino.mkdir(parents=True, exist_ok=True)
    captions = []
    for pieza in sorted(p for p in lote_dir.iterdir() if p.is_dir()):
        for archivo in sorted(pieza.iterdir()):
            if archivo.suffix in (".png", ".mp4"):
                shutil.copy(archivo, destino / f"{pieza.name}__{archivo.name}")
        cap = pieza / "caption.txt"
        if cap.exists():
            captions.append(f"===== {pieza.name} =====\n{cap.read_text(encoding='utf-8')}\n")
    (destino / "00-CAPTIONS.txt").write_text("\n".join(captions), encoding="utf-8")
```

- [ ] **Step 2: Write `src/main.py`**

```python
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
from pathlib import Path

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
    for tipo in elegidos_ev:
        banco, _ = TIPOS[tipo]
        item = seleccionar(cfg, banco, 1, seed + hash(tipo) % 1000)[0]
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
    placas = [{"plantilla": "portada", "tag": tag, "titulo": red["titulo_portada"]}]
    for i, b in enumerate(red["ideas"], start=1):
        placas.append({"plantilla": plantilla_idea, "numero": i,
                       "titulo": b["titulo"], "texto": b["texto"]})
    if tipo == "tip" and red.get("codigo"):
        placas.append({"plantilla": "codigo", "lenguaje": red.get("lenguaje", "sql"),
                       "codigo": red["codigo"]})
    placas.append({"plantilla": "cierre"})
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
```

- [ ] **Step 3: Write the failing tests** — `tests/test_exportar.py` and `tests/test_main.py`

`tests/test_exportar.py`:
```python
from src import exportar


def test_exportar_aplana_y_junta_captions(tmp_path):
    lote = tmp_path / "semana-2026-07-05"
    pieza = lote / "01-novedad"
    pieza.mkdir(parents=True)
    (pieza / "01.png").write_bytes(b"x" * 50)
    (pieza / "caption.txt").write_text("hola", encoding="utf-8")
    destino = tmp_path / "ParaSubir"
    exportar.exportar(lote, destino)
    assert (destino / "01-novedad__01.png").exists()
    assert "hola" in (destino / "00-CAPTIONS.txt").read_text(encoding="utf-8")
```

`tests/test_main.py`:
```python
from src import main
from src.config import get_config


def test_plan_semana_sin_novedad_da_tres_evergreen(monkeypatch, tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    piezas = main.plan_semana(cfg, seed=202627, novedad=None)
    assert len(piezas) == 3
    assert all(p["tipo"] in cfg.tipos_evergreen for p in piezas)


def test_plan_semana_con_novedad(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    nov = {"id": "http://x/1", "titulo": "T", "resumen": "R", "link": "http://x/1", "fuente": "PBI"}
    piezas = main.plan_semana(cfg, seed=202627, novedad=nov)
    assert piezas[0]["tipo"] == "novedad"
    assert len(piezas) == 3  # 1 novedad + 2 evergreen


def test_construir_placas_tip_incluye_codigo():
    red = {"titulo_portada": "X", "ideas": [{"titulo": "a", "texto": "b"}],
           "codigo": "SELECT 1;", "lenguaje": "sql"}
    placas = main.construir_placas("tip", red)
    plantillas = [p["plantilla"] for p in placas]
    assert "codigo" in plantillas
    assert plantillas[0] == "portada" and plantillas[-1] == "cierre"


def test_armar_caption_agrega_ctas_y_hashtags():
    cap = main.armar_caption("cuerpo", ["data", "sql"])
    assert "cuerpo" in cap and "#data" in cap
    from src import config
    assert config.CTA_GUARDAR in cap
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ROOT && python -m pytest tests/test_main.py tests/test_exportar.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Run the full dry-run end-to-end**

Run: `cd ROOT && python -m src.main --dry-run`
Expected: exit 0; creates `salida/semana-<hoy>/01-novedad/` … `04-tip/` each with PNGs + `caption.txt` + `meta.json`, plus `salida/ParaSubir/semana-<hoy>/00-CAPTIONS.txt`. Open a couple of PNGs to eyeball the dark theme.

- [ ] **Step 6: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: orchestrator + manual export (dry-run works end-to-end)"
```

---

### Task 8: Workflow, docs, and full-suite green

**Files:**
- Create: `.github/workflows/contenido.yml`, `README.md`, `MANUAL-TECNICO.md`
- Modify: `estado/usados.json`, `estado/fuente_vista.json` (seed empty state)

**Interfaces:** none (integration + docs).

- [ ] **Step 1: Seed empty state files**

Create `estado/usados.json` with `{}` and `estado/fuente_vista.json` with `[]` so the first run and the tests have a stable base. Add `salida/` to `.gitignore` (already present from Task 1's scaffold; confirm).

- [ ] **Step 2: Write `.github/workflows/contenido.yml`**

Read `REF/.github/workflows/contenido.yml` for the exact rclone/BOM handling and Drive step, then create this adapted version (no publisher, no manifiesto):

```yaml
name: Generar contenido Data Snake
on:
  workflow_dispatch:
  schedule:
    - cron: "0 11 * * 0"   # domingos 11:00 UTC = 08:00 ARG
jobs:
  generar:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: python -m playwright install --with-deps chromium
      - run: sudo apt-get update && sudo apt-get install -y rclone ffmpeg
      - name: Generar lote
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python -m src.main
      - name: Subir a Drive
        env:
          RCLONE_CONFIG_GDRIVE_TYPE: drive
          RCLONE_CONFIG_GDRIVE_SCOPE: drive
          GDRIVE_TOKEN: ${{ secrets.GDRIVE_TOKEN }}
          RCLONE_CONFIG_GDRIVE_ROOT_FOLDER_ID: ${{ secrets.GDRIVE_FOLDER_ID }}
        run: |
          export RCLONE_CONFIG_GDRIVE_TOKEN="{${GDRIVE_TOKEN#*\{}"
          rclone copy salida/ gdrive: --exclude "**/00-CAPTIONS.txt" || echo "Drive falló"
          rclone copy salida/ gdrive: --include "**/00-CAPTIONS.txt" \
            --drive-import-formats txt --drive-export-formats txt || true
      - name: Guardar lote como artifact (respaldo)
        if: always()
        uses: actions/upload-artifact@v4
        with: { name: lote, path: salida/, retention-days: 14 }
      - name: Commitear estado
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add estado/*.json
          git commit -m "estado: corrida $(date +%F)" || echo "sin cambios"
          git push || echo "sin push"
```
> Confirm the `RCLONE_CONFIG_GDRIVE_TOKEN` BOM-trim line matches REF's; copy REF's exact line if it differs.

- [ ] **Step 3: Write `README.md` and `MANUAL-TECNICO.md`**

`README.md` — short: what it is (weekly $0 content factory for `@data.snake`, generate-and-post-by-hand), how to run local (`pip install -r requirements.txt`, `python -m playwright install chromium`, `pytest`, `python -m src.main --dry-run`), and a pointer to `MANUAL-TECNICO.md`.

`MANUAL-TECNICO.md` — living manual with: the 30-second summary, the generation flow (source → Gemini → render → export → Drive), the 4 piece types + their banks/feeds, and a **knobs table** covering at minimum: cron (`contenido.yml`), mix (`config.py MIX_NOVEDAD`/`TIPOS_EVERGREEN`), voice (`prompts.py VOZ_DE_MARCA`), palette (`config.py COLOR_*`), eslogan/handle/CTAs (`config.py`), hashtags (`HASHTAGS_DEFAULT`), feeds (`datos/feeds.json`), freshness (`config.py FRESCURA_DIAS`), banks (`datos/*.json`), templates (`plantillas/*.html`), reel seconds (`config.py SEGUNDOS_POR_SLIDE`). End with an "Última actualización" date line.

- [ ] **Step 4: Run the full test suite**

Run: `cd ROOT && python -m pytest -q`
Expected: all tests PASS (config, bancos, feeds, prompts, contratos, render, reel_slideshow, main, exportar).

- [ ] **Step 5: Commit**

```bash
cd ROOT && git add -A && git commit -m "feat: Actions workflow + README + technical manual"
```

---

## Self-Review

**1. Spec coverage:**
- §3 architecture (generation + delivery, no Part B) → Tasks 1–8; publisher/responder never created. ✅
- §4 four piece types + mix + fallback → Task 7 `plan_semana`/`construir_placas`/`plan_b`. ✅
- §5 components → each mapped to a task (config T1, bancos T2, feeds T3, gemini/prompts/contratos T4, renderer+templates T5, reel T6, main/exportar T7, workflow T8). ✅
- §6 scraper RSS-first + freshness + dedup + plan B → Task 3. ✅
- §7 dark templates incl. `codigo.html` → Task 5. ✅
- §8 voice voseo, JSON contracts, plan B → Task 4 + Task 7. ✅
- §10 Drive delivery + ParaSubir, no `Publicado/` → Task 7 export + Task 8 workflow. ✅
- §11 secrets (only 3) + state files → Task 8 workflow + state seed. ✅
- §2 brand palette/eslogan/handle → Task 1 config + Task 5 templates. ✅
- §14 deps incl. feedparser, no edge-tts → Task 1 requirements. ✅

**2. Placeholder scan:** No "TBD"/"add error handling as needed"; every code step has full code. The two soft spots (music function name in Task 6, rclone BOM line in Task 8) explicitly instruct reading the REF file and adapting — not silent placeholders. ✅

**3. Type consistency:** `elegir_novedad` returns `{"id","titulo","resumen","link","fuente"}` (T3) — consumed the same way in `plan_semana`/`plan_b`/`registrar_vista` (T7). `validar(tipo, datos)` fields match what `prompts` request and what `construir_placas` reads (`titulo_portada`, `ideas[].titulo/texto`, `codigo`, `lenguaje`, `caption`, `hashtags`). `generar_reel(carpeta, cfg, seed)` signature matches its one call site. `Renderer.render_placa(contexto, destino)` matches T5. ✅

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-03-datasnake-contenido.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
