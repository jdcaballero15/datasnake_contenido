# Placas densas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que cada placa de contenido del carrusel se vea como la referencia (`referencia/Captura*.png`): densa, con título condensado gigante, deck y un panel de secciones etiquetadas — en vez de la placa medio vacía de hoy.

**Architecture:** Una idea deja de ser `{titulo, texto}` y pasa a ser `{titulo, deck, secciones:[…]}`. Un módulo nuevo, `src/contenido.py`, es el dueño único de ese modelo: define los labels fijos por tipo, arma ideas densas desde un item de banco (plan B, sin IA) y hace de puente mientras Gemini todavía devuelve el formato viejo. Las 3 plantillas de contenido (`idea`, `comparativa`, `codigo`) se funden en una sola, `contenido.html`. El código deja de tener placa propia: es una sección más.

**Tech Stack:** Python 3.12, Jinja2, Playwright/Chromium, pytest. Google Fonts (Anton, Archivo, JetBrains Mono).

## Global Constraints

- Spec de referencia: `docs/superpowers/specs/2026-07-13-placas-densas-design.md`.
- **Dos desvíos del spec, ya acordados con el dueño de la cuenta** (actualizar el spec en la Tarea 1):
  - `rol` NO lleva sección `➤ SUELDO` (los bancos no traen sueldos y `VOZ_DE_MARCA` prohíbe inventar números). Cada placa de un `rol` es **una skill del rol**, con secciones `➤ POR QUÉ TE LA PIDEN` / `➤ CÓMO LA PRACTICÁS`.
  - El `veredicto` de una comparativa no entra en las placas (las secciones son fijas): sigue viviendo en el caption.
- Labels de sección **fijos por tipo, definidos en el código** (`SECCIONES_POR_TIPO`). El contenido nunca elige sus labels.
- Paleta: solo colores ya existentes en `src/config.py` + el hueso `#EEE9E1`. Nada de naranja.
- Tipografía: **Anton** (títulos), **Archivo** (deck y cuerpo), **JetBrains Mono** (código).
- Idioma de todo el contenido y los labels: español rioplatense (voseo), como `VOZ_DE_MARCA` en `src/redaccion/prompts.py`.
- Placas: 1080×1350. Los tests corren con `.venv/Scripts/python.exe -m pytest` (Windows).
- Cada tarea termina con commit. Los tests deben quedar en verde al final de cada tarea.

---

### Task 1: Modelo de contenido (labels fijos + puente legacy)

**Files:**
- Create: `src/contenido.py`
- Create: `tests/test_contenido.py`
- Modify: `docs/superpowers/specs/2026-07-13-placas-densas-design.md` (los dos desvíos de Global Constraints)

**Interfaces:**
- Consumes: nada (módulo hoja).
- Produces:
  - `SECCIONES_POR_TIPO: dict[str, list[str]]` — labels fijos por tipo.
  - `KICKER_POR_TIPO: dict[str, str]` — palabra del kicker por tipo (`"cambio"`, `"opción"`, `"skill"`, `"tip"`).
  - `normalizar_ideas(tipo: str, red: dict) -> list[dict]` — devuelve ideas densas; si la idea ya trae `secciones`, la deja pasar tal cual; si viene en el formato viejo (`{titulo, texto}`), la envuelve en una sección con el primer label del tipo. Para `tip`, si `red` trae `codigo`, le agrega la sección de código a la primera idea.
  - Forma de una idea densa: `{"titulo": str, "deck": str, "secciones": [seccion]}` donde una sección es `{"label": str, "texto": str}` **o** `{"label": str, "codigo": str, "lenguaje": str}`.

- [ ] **Step 1: Write the failing test**

Crear `tests/test_contenido.py`:

```python
from src import contenido


def test_labels_fijos_por_tipo():
    assert contenido.SECCIONES_POR_TIPO["comparativa"] == ["cuándo conviene", "dónde duele"]
    assert contenido.SECCIONES_POR_TIPO["rol"] == ["por qué te la piden", "cómo la practicás"]
    assert contenido.SECCIONES_POR_TIPO["tip"] == ["el problema", "el código", "por qué funciona"]
    assert contenido.SECCIONES_POR_TIPO["novedad"] == ["qué cambió", "por qué importa"]


def test_normalizar_envuelve_idea_vieja_en_una_seccion():
    red = {"ideas": [{"titulo": "Copilot", "texto": "Genera DAX en lenguaje natural."}]}

    ideas = contenido.normalizar_ideas("novedad", red)

    assert ideas == [{
        "titulo": "Copilot",
        "deck": "",
        "secciones": [{"label": "qué cambió", "texto": "Genera DAX en lenguaje natural."}],
    }]


def test_normalizar_deja_pasar_idea_ya_densa():
    idea = {"titulo": "Excel", "deck": "Limpiar 10.000 filas",
            "secciones": [{"label": "cuándo conviene", "texto": "Algo puntual."}]}

    ideas = contenido.normalizar_ideas("comparativa", {"ideas": [idea]})

    assert ideas == [idea]


def test_normalizar_tip_agrega_seccion_de_codigo():
    red = {"ideas": [{"titulo": "Top N", "texto": "ROW_NUMBER con PARTITION BY."}],
           "codigo": "SELECT 1;", "lenguaje": "sql"}

    secciones = contenido.normalizar_ideas("tip", red)[0]["secciones"]

    assert secciones[1] == {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_contenido.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.contenido'`

- [ ] **Step 3: Write minimal implementation**

Crear `src/contenido.py`:

```python
"""Modelo de contenido de una placa densa: título + deck + secciones etiquetadas.

Los labels de sección son FIJOS por tipo y viven acá: ni el banco ni Gemini los
eligen. Eso es lo que hace que el carrusel se lea igual semana a semana.
"""

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


def normalizar_ideas(tipo: str, red: dict) -> list[dict]:
    """Puente: Gemini todavía devuelve {titulo, texto}. Lo envuelve en el modelo
    denso para que la plantilla no tenga que saber de qué época viene el dato.
    Se elimina en la etapa 2, cuando Gemini devuelva secciones."""
    ideas = []
    for idea in red.get("ideas", []):
        if "secciones" in idea:
            ideas.append(idea)
            continue
        ideas.append({
            "titulo": idea.get("titulo", ""),
            "deck": idea.get("deck", ""),
            "secciones": [{"label": SECCIONES_POR_TIPO[tipo][0],
                           "texto": idea.get("texto", "")}],
        })
    if tipo == "tip" and red.get("codigo") and ideas:
        ideas[0]["secciones"].append({
            "label": "el código",
            "codigo": red["codigo"],
            "lenguaje": red.get("lenguaje", "sql"),
        })
    return ideas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_contenido.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Actualizar el spec con los dos desvíos**

En `docs/superpowers/specs/2026-07-13-placas-densas-design.md`, en la tabla de labels por tipo, reemplazar la fila de `rol` por:

```markdown
| `rol` | ➤ POR QUÉ TE LA PIDEN · ➤ CÓMO LA PRACTICÁS (cada placa es una skill del rol) |
```

Y agregar, debajo de la tabla:

```markdown
Descartado: la sección `➤ SUELDO` del borrador inicial. Los bancos no traen sueldos y
`VOZ_DE_MARCA` prohíbe inventar números, así que solo se podría llenar inventando.
El `veredicto` de una comparativa tampoco entra en las placas (las secciones son fijas):
sigue viviendo en el caption.
```

- [ ] **Step 6: Commit**

```bash
git add src/contenido.py tests/test_contenido.py docs/superpowers/specs/2026-07-13-placas-densas-design.md
git commit -m "feat: modelo de contenido denso (labels fijos por tipo)"
```

---

### Task 2: Banco de comparativas con opciones ricas

Hoy una opción es un string suelto (`"Excel: filtros + quitar duplicados, ~8 pasos manuales"`). Para llenar las dos secciones fijas de `comparativa` hace falta partirla en `nombre` + `cuando_conviene` + `donde_duele`.

**Files:**
- Modify: `datos/comparativas.json` (los 15 items)
- Create: `tests/test_datos.py`

**Interfaces:**
- Consumes: nada.
- Produces: esquema de item de `comparativas.json`:
  `{"id": str, "tarea": str, "opciones": [{"nombre": str, "cuando_conviene": str, "donde_duele": str}], "veredicto": str}`

- [ ] **Step 1: Write the failing test**

Crear `tests/test_datos.py`:

```python
import json

from src.config import get_config


def _banco(nombre):
    ruta = get_config().dir_datos / f"{nombre}.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def test_comparativas_tienen_opciones_ricas():
    items = _banco("comparativas")
    assert len(items) == 15
    for item in items:
        assert item["id"] and item["tarea"] and item["veredicto"]
        assert len(item["opciones"]) >= 2
        for opcion in item["opciones"]:
            assert opcion["nombre"], f"{item['id']}: opción sin nombre"
            assert len(opcion["cuando_conviene"]) >= 30, f"{item['id']}: cuando_conviene pobre"
            assert len(opcion["donde_duele"]) >= 30, f"{item['id']}: donde_duele pobre"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_datos.py -v`
Expected: FAIL — `TypeError: string indices must be integers` (las opciones todavía son strings)

- [ ] **Step 3: Reescribir `datos/comparativas.json`**

Cada item pasa de opciones-string a opciones-objeto. Los dos primeros, completos, como molde exacto (el resto de los 13 se escribe igual, conservando `id`, `tarea` y `veredicto` actuales y repartiendo la info del string viejo en `nombre` + `cuando_conviene`, e inventando el `donde_duele` desde el conocimiento técnico real de la herramienta — nunca números ni benchmarks):

```json
[
  {"id": "c01", "tarea": "Limpiar 10.000 filas con nulos y duplicados",
   "opciones": [
     {"nombre": "Excel",
      "cuando_conviene": "Es una limpieza de una sola vez y querés verla con los ojos: filtros, quitar duplicados y listo.",
      "donde_duele": "Son ~8 pasos manuales que nadie deja documentados: la semana que viene los repetís de memoria y no sabés si te dio distinto."},
     {"nombre": "Python / pandas",
      "cuando_conviene": "La limpieza se repite: dropna y drop_duplicates son 3 líneas que corrés igual todos los meses.",
      "donde_duele": "Necesitás el entorno armado y que alguien más pueda correrlo; para un archivo suelto es matar una mosca a cañonazos."},
     {"nombre": "SQL",
      "cuando_conviene": "Los datos ya viven en la base: WHERE y DISTINCT resuelven en el server, sin bajar nada.",
      "donde_duele": "Si el dato todavía no está cargado, primero tenés que ingestarlo, y ahí ya perdiste la ventaja."}],
   "veredicto": "Para algo puntual, Excel; para algo repetible, pandas o SQL."},
  {"id": "c02", "tarea": "Un dashboard que se actualice solo",
   "opciones": [
     {"nombre": "Power BI",
      "cuando_conviene": "Querés refresh programado y publicar al Service para que el equipo lo abra sin pedirte nada.",
      "donde_duele": "El refresh automático depende del gateway y de licencias: el día que falla, te enterás por el usuario."},
     {"nombre": "Tableau",
      "cuando_conviene": "Necesitás exploración visual fuerte y elegir entre extract programado o conexión en vivo.",
      "donde_duele": "El costo por usuario pesa, y la curva para hacer cálculos finos es más empinada que en Power BI."},
     {"nombre": "Excel",
      "cuando_conviene": "El equipo ya vive en Excel: Power Query te deja refrescar sin cambiarles la herramienta.",
      "donde_duele": "Alguien tiene que apretar refrescar (o mantener una macro), así que de \"solo\" tiene poco."}],
   "veredicto": "Power BI/Tableau para producción; Excel solo si el equipo ya lo usa."}
]
```

Reglas para los 13 restantes: `nombre` es la herramienta sola (sin descripción); `cuando_conviene` y `donde_duele` son 1–2 oraciones en voseo, concretas, sin números inventados; ambas ≥30 caracteres (el test lo exige).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_datos.py -v`
Expected: PASS

- [ ] **Step 5: Verificar que el resto de la suite sigue verde**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: los tests de bancos/main/prompts pasan (todavía nadie lee `opciones` como objeto salvo el test nuevo). Si `tests/test_prompts.py` o `src/redaccion/prompts.py:prompt_comparativa` fallan al hacer `"\n".join(f"- {o}" for o in item["opciones"])`, corregir ese join a:

```python
opciones = "\n".join(
    f"- {o['nombre']}: conviene si {o['cuando_conviene']} Duele en que {o['donde_duele']}"
    for o in item["opciones"])
```

- [ ] **Step 6: Commit**

```bash
git add datos/comparativas.json tests/test_datos.py src/redaccion/prompts.py
git commit -m "feat: comparativas con cuando_conviene y donde_duele por opción"
```

---

### Task 3: Banco de roles con skills ricas

Cada placa de un `rol` es **una skill**. Hoy `skills` es una lista de strings (`"SQL sólido"`), que no llena ninguna sección.

**Files:**
- Modify: `datos/roles.json` (los 15 items)
- Modify: `tests/test_datos.py` (agregar test del banco de roles)
- Modify: `src/redaccion/prompts.py:prompt_rol` (el join de skills)

**Interfaces:**
- Consumes: nada.
- Produces: esquema de item de `roles.json`:
  `{"id": str, "rol": str, "gancho": str, "herramientas": [str], "skills": [{"nombre": str, "por_que": str, "como_practicar": str}]}`

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_datos.py`:

```python
def test_roles_tienen_skills_ricas():
    items = _banco("roles")
    assert len(items) == 15
    for item in items:
        assert item["id"] and item["rol"] and item["gancho"]
        assert item["herramientas"]
        assert len(item["skills"]) >= 3
        for skill in item["skills"]:
            assert skill["nombre"], f"{item['id']}: skill sin nombre"
            assert len(skill["por_que"]) >= 30, f"{item['id']}: por_que pobre"
            assert len(skill["como_practicar"]) >= 30, f"{item['id']}: como_practicar pobre"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_datos.py::test_roles_tienen_skills_ricas -v`
Expected: FAIL — `TypeError: string indices must be integers`

- [ ] **Step 3: Reescribir `datos/roles.json`**

Molde exacto (primer item completo; los otros 14 se escriben igual, conservando `id`, `rol`, `gancho` y `herramientas` actuales):

```json
[
  {"id": "r01", "rol": "Data Analyst",
   "gancho": "El puente entre los datos crudos y la decisión de negocio.",
   "herramientas": ["SQL", "Power BI", "Excel", "Python"],
   "skills": [
     {"nombre": "SQL",
      "por_que": "Es el idioma en el que están los datos: sin SQL dependés de que alguien te pase un export.",
      "como_practicar": "Agarrá una base pública y respondé preguntas de negocio con JOIN, GROUP BY y window functions, sin exportar a Excel."},
     {"nombre": "Una herramienta de BI",
      "por_que": "Nadie decide mirando una tabla: el dashboard es el formato en el que tu trabajo se consume.",
      "como_practicar": "Rehacé un reporte que hoy vive en Excel como un dashboard de Power BI, con filtros y una medida propia."},
     {"nombre": "Comunicar hallazgos",
      "por_que": "Un análisis que no se entiende no existe: te van a medir por la decisión que gatillaste, no por la query.",
      "como_practicar": "Contá cada análisis en tres frases: qué preguntaste, qué encontraste, qué habría que hacer."}]}
]
```

Reglas para los 14 restantes: 3–4 skills por rol; `nombre` corto (entra como título gigante en la placa); `por_que` y `como_practicar` en voseo, concretas, sin números inventados; ambas ≥30 caracteres.

- [ ] **Step 4: Arreglar el prompt de rol**

En `src/redaccion/prompts.py:prompt_rol`, reemplazar:

```python
    skills = ", ".join(item["skills"])
```

por:

```python
    skills = "\n".join(
        f"- {s['nombre']}: te la piden porque {s['por_que']} Se practica así: {s['como_practicar']}"
        for s in item["skills"])
```

y en el cuerpo del prompt cambiar la línea `Skills: {skills}` por:

```
Skills:
{skills}
```

- [ ] **Step 5: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_datos.py tests/test_prompts.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add datos/roles.json tests/test_datos.py src/redaccion/prompts.py
git commit -m "feat: roles con skills ricas (por_que y como_practicar)"
```

---

### Task 4: Ideas densas desde el banco (plan B sin IA)

**Files:**
- Modify: `src/contenido.py` (agregar `ideas_desde_item`)
- Modify: `tests/test_contenido.py`

**Interfaces:**
- Consumes: `SECCIONES_POR_TIPO` (Task 1); esquemas de banco de Tasks 2 y 3; `datos/tips.json` (sin cambios: `titulo`, `gancho`, `codigo`, `lenguaje`, `explicacion`).
- Produces: `ideas_desde_item(tipo: str, item: dict) -> list[dict]` — ideas densas armadas solo con el material del banco/feed, sin IA. La usa `src/main.py:plan_b` (Task 6).

- [ ] **Step 1: Write the failing test**

Agregar a `tests/test_contenido.py`:

```python
def test_ideas_desde_item_comparativa_una_idea_por_opcion():
    item = {"tarea": "Limpiar 10.000 filas", "veredicto": "Depende.", "opciones": [
        {"nombre": "Excel", "cuando_conviene": "Una sola vez.", "donde_duele": "No queda documentado."},
        {"nombre": "pandas", "cuando_conviene": "Se repite.", "donde_duele": "Necesitás entorno."}]}

    ideas = contenido.ideas_desde_item("comparativa", item)

    assert [i["titulo"] for i in ideas] == ["Excel", "pandas"]
    assert ideas[0]["deck"] == "Limpiar 10.000 filas"
    assert ideas[0]["secciones"] == [
        {"label": "cuándo conviene", "texto": "Una sola vez."},
        {"label": "dónde duele", "texto": "No queda documentado."},
    ]


def test_ideas_desde_item_rol_una_idea_por_skill():
    item = {"rol": "Data Analyst", "gancho": "El puente al negocio.", "herramientas": ["SQL"],
            "skills": [{"nombre": "SQL", "por_que": "Es el idioma.", "como_practicar": "Base pública."}]}

    ideas = contenido.ideas_desde_item("rol", item)

    assert ideas[0]["titulo"] == "SQL"
    assert ideas[0]["deck"] == "El puente al negocio."
    assert [s["label"] for s in ideas[0]["secciones"]] == ["por qué te la piden", "cómo la practicás"]


def test_ideas_desde_item_tip_tiene_las_tres_secciones_con_codigo():
    item = {"titulo": "Top N en SQL", "gancho": "Top N por grupo en una pasada.",
            "codigo": "SELECT 1;", "lenguaje": "sql", "explicacion": "ROW_NUMBER numera por grupo."}

    idea = contenido.ideas_desde_item("tip", item)[0]

    assert idea["titulo"] == "Top N en SQL"
    assert [s["label"] for s in idea["secciones"]] == ["el problema", "el código", "por qué funciona"]
    assert idea["secciones"][1] == {"label": "el código", "codigo": "SELECT 1;", "lenguaje": "sql"}


def test_ideas_desde_item_novedad_usa_el_resumen():
    item = {"titulo": "Power BI suma Copilot", "resumen": "Genera DAX en lenguaje natural.",
            "fuente": "Power BI Blog", "link": "http://x/1", "id": "http://x/1"}

    idea = contenido.ideas_desde_item("novedad", item)[0]

    assert idea["secciones"][0] == {"label": "qué cambió", "texto": "Genera DAX en lenguaje natural."}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_contenido.py -v`
Expected: FAIL — `AttributeError: module 'src.contenido' has no attribute 'ideas_desde_item'`

- [ ] **Step 3: Write the implementation**

Agregar a `src/contenido.py`:

```python
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
        return [{
            "titulo": item["titulo"],
            "deck": "",
            "secciones": [
                {"label": "el problema", "texto": item["gancho"]},
                {"label": "el código", "codigo": item["codigo"],
                 "lenguaje": item.get("lenguaje", "sql")},
                {"label": "por qué funciona", "texto": item["explicacion"]},
            ],
        }]

    return [{
        "titulo": item["titulo"],
        "deck": item.get("fuente", ""),
        "secciones": [
            {"label": "qué cambió", "texto": item["resumen"]},
            {"label": "por qué importa",
             "texto": "Una novedad para tener en el radar si trabajás con esta herramienta."},
        ],
    }]
```

- [ ] **Step 4: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_contenido.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add src/contenido.py tests/test_contenido.py
git commit -m "feat: ideas densas desde el material del banco"
```

---

### Task 5: Sistema visual (Anton, portada verde, placa clara, plantilla única)

**Files:**
- Modify: `src/config.py` (agregar `COLOR_HUESO`)
- Modify: `src/render/renderer.py` (pasar `hueso` en `c`; sacar el default de `module_label`)
- Rewrite: `plantillas/_estilos.html`
- Rewrite: `plantillas/portada.html`, `plantillas/cierre.html`
- Create: `plantillas/contenido.html`
- Delete: `plantillas/idea.html`, `plantillas/comparativa.html`, `plantillas/codigo.html`
- Modify: `tests/test_render.py`

**Interfaces:**
- Consumes: forma de idea densa (Task 1).
- Produces: contrato de contexto de `contenido.html` — `{plantilla: "contenido", kicker: str, titulo: str, deck: str, secciones: [seccion], variant: "dark"|"light", slide_index, slide_total}`. `portada.html` consume `{tag, titulo, subtitulo, variant: "cover"}`. `cierre.html` consume `{variant: "close"}`.

- [ ] **Step 1: Write the failing test**

Reemplazar **todo** `tests/test_render.py` por:

```python
from src.config import get_config
from src.render.renderer import Renderer

C = {"fondo": "#111827", "texto": "#CBD5E1", "acento": "#2A7FA8", "borde": "#253347",
     "surface": "#1C2B3A", "texto_sec": "#7B91A8", "grad_a": "#7C5CBF",
     "grad_b": "#2EE6A6", "hueso": "#EEE9E1"}

SECCIONES = [
    {"label": "el problema", "texto": "Top N por grupo sin subconsultas."},
    {"label": "el código", "codigo": "SELECT * FROM t WHERE a <> b & c;", "lenguaje": "sql"},
    {"label": "por qué funciona", "texto": "ROW_NUMBER numera dentro de cada grupo."},
]

PLACAS = [
    {"plantilla": "portada", "tag": "Tip", "titulo": "TOP N\nEN SQL",
     "subtitulo": "Herramientas, resultados y carrera en data", "variant": "cover"},
    {"plantilla": "contenido", "kicker": "tip 01", "titulo": "TOP N EN SQL",
     "deck": "Sin subconsultas.", "secciones": SECCIONES, "variant": "dark"},
    {"plantilla": "contenido", "kicker": "opción 03", "titulo": "PANDAS",
     "deck": "Limpiar 10.000 filas.", "secciones": SECCIONES[:1], "variant": "light"},
    {"plantilla": "cierre", "variant": "close"},
]


def test_render_cada_plantilla_produce_png(tmp_path):
    cfg = get_config()
    with Renderer(cfg) as r:
        for i, ctx in enumerate(PLACAS, start=1):
            destino = tmp_path / f"{i:02d}.png"
            r.render_placa(ctx, destino)
            assert destino.exists() and destino.stat().st_size > 1000


def _render(name, **extra):
    ctx = {"kicker": "tip 01", "titulo": "TOP N EN SQL", "deck": "Sin subconsultas.",
           "secciones": SECCIONES, "tag": "Tip", "subtitulo": "Eslogan",
           "slide_index": 2, "slide_total": 4, "variant": "dark", "c": C,
           "logo_uri": "data:,", "ig_handle": "data.snake",
           "eslogan": "Herramientas, resultados y carrera en data"}
    ctx.update(extra)
    return Renderer(get_config()).env.get_template(f"{name}.html").render(**ctx)


def test_contenido_tiene_shell_de_carrusel():
    html = _render("contenido")
    assert 'class="plate variant-dark"' in html
    assert 'class="plate-header"' in html
    assert "02 / 04" in html
    assert 'class="progress-dot active"' in html
    assert "DESLIZA" in html and "GUARDAR" in html


def test_contenido_pinta_todas_las_secciones_con_su_label():
    html = _render("contenido")
    assert "EL PROBLEMA" in html
    assert "EL CÓDIGO" in html
    assert "POR QUÉ FUNCIONA" in html
    assert html.count('class="section-label"') == 3


def test_contenido_escapa_el_codigo():
    html = _render("contenido")
    assert 'class="code-text"' in html
    assert "&lt;&gt;" in html and "&amp;" in html
    assert "<> b & c" not in html  # los caracteres crudos no pueden filtrarse


def test_variante_clara_existe():
    html = _render("contenido", variant="light")
    assert 'class="plate variant-light"' in html


def test_portada_usa_variante_cover():
    html = _render("portada", variant="cover")
    assert 'class="plate variant-cover"' in html
    assert "TOP N" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_render.py -v`
Expected: FAIL — `jinja2.exceptions.TemplateNotFound: contenido.html`

- [ ] **Step 3: Agregar el hueso a la paleta**

En `src/config.py`, debajo de `GRAD_B`:

```python
COLOR_HUESO = "#EEE9E1"        # fondo de la placa clara
```

En `src/render/renderer.py`: agregar `COLOR_HUESO` al import desde `src.config`, agregar `"hueso": COLOR_HUESO` al dict `c` del `setdefault`, y **borrar** la línea `contexto.setdefault("module_label", "qué resuelve")` (ese concepto ya no existe).

- [ ] **Step 4: Reescribir `plantillas/_estilos.html`**

```html
<style>
  @import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@500;700;900&family=JetBrains+Mono:wght@400;600&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:1080px; height:1350px; }
  body { width:1080px; height:1350px; overflow:hidden; font-family:'Archivo',system-ui,sans-serif; }

  .plate {
    width:1080px; height:1350px; padding:72px 76px 64px;
    display:flex; flex-direction:column; position:relative; overflow:hidden;
  }
  .variant-cover { background:{{ c.grad_b }}; color:#0B1F1A; }
  .variant-dark, .variant-close { background:{{ c.fondo }}; color:{{ c.texto }}; }
  .variant-light { background:{{ c.hueso }}; color:#111827; }

  .plate-header {
    display:flex; justify-content:space-between; align-items:center;
    font-size:26px; font-weight:700; opacity:.85;
  }
  .plate-footer {
    margin-top:auto; display:flex; justify-content:space-between; align-items:center;
    font-size:22px; letter-spacing:.14em; text-transform:uppercase; font-weight:900; opacity:.9;
  }
  .progress { display:flex; gap:10px; align-items:center; }
  .progress-dot { width:10px; height:10px; border-radius:50%; background:currentColor; opacity:.3; }
  .progress-dot.active { opacity:1; }

  /* El contenido arranca arriba y BAJA llenando: nada de margin-top:auto acá
     (eso era lo que dejaba media placa vacía en el diseño anterior). */
  .kicker {
    margin-top:40px; font-size:24px; letter-spacing:.2em; text-transform:uppercase;
    font-weight:900; color:{{ c.grad_b }};
  }
  .variant-light .kicker { color:{{ c.grad_a }}; }
  .variant-cover .kicker { color:#0B1F1A; }

  .title {
    font-family:'Anton',Impact,sans-serif; font-weight:400; text-transform:uppercase;
    line-height:.94; letter-spacing:.01em; margin-top:16px; font-size:118px; white-space:pre-line;
  }
  .title-medium { font-size:94px; }
  .variant-dark .title { color:{{ c.grad_b }}; }
  .variant-light .title { color:{{ c.grad_a }}; }

  .deck { margin-top:20px; font-size:38px; line-height:1.2; font-weight:700; max-width:900px; }
  .variant-dark .deck { color:#FFFFFF; }
  .cover-deck { margin-top:26px; font-size:34px; font-weight:500; line-height:1.3; max-width:820px; }

  .panel {
    margin-top:34px; background:{{ c.surface }}; border:2px solid {{ c.borde }};
    border-radius:24px; padding:34px 38px;
  }
  .variant-light .panel { background:{{ c.fondo }}; border-color:{{ c.fondo }}; }
  .section + .section { margin-top:26px; }
  .section-label {
    font-size:23px; letter-spacing:.16em; text-transform:uppercase; font-weight:900;
    color:{{ c.grad_b }}; margin-bottom:10px;
  }
  .section-text { font-size:33px; line-height:1.34; color:{{ c.texto }}; }

  .code-block { background:#07111D; border:1px solid #102034; border-radius:16px; padding:22px 24px; }
  .code-top { font-family:'JetBrains Mono',monospace; font-size:20px; color:#58708A; margin-bottom:14px; }
  .code-text {
    font-family:'JetBrains Mono',monospace; font-size:27px; line-height:1.45;
    color:#9FB2C7; white-space:pre-wrap; word-break:break-word;
  }

  .cover-mark {
    position:absolute; right:-90px; bottom:150px; width:320px; height:320px;
    border:30px solid rgba(11,31,26,.12); border-radius:50%;
  }
  .brand-logo { width:120px; height:120px; object-fit:contain; }
  .close-mark { margin-top:40px; display:flex; align-items:center; gap:22px; }
  .close-copy { margin-top:34px; font-size:44px; line-height:1.2; color:{{ c.texto_sec }}; }
  .close-copy strong { color:{{ c.texto }}; }
</style>
```

- [ ] **Step 5: Crear `plantillas/contenido.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index|default(1)) }} / {{ "%02d"|format(slide_total|default(1)) }}</span>
  </header>
  <div class="kicker">— {{ kicker }}</div>
  <h2 class="title title-medium">{{ titulo }}</h2>
  {% if deck %}<p class="deck">{{ deck }}</p>{% endif %}
  <section class="panel">
    {% for s in secciones %}
    <div class="section">
      <div class="section-label">➤ {{ s.label|upper }}</div>
      {% if s.codigo %}
      <div class="code-block">
        <div class="code-top">data.snake · {{ s.lenguaje|default("sql") }}</div>
        <pre class="code-text">{{ s.codigo }}</pre>
      </div>
      {% else %}
      <p class="section-text">{{ s.texto }}</p>
      {% endif %}
    </div>
    {% endfor %}
  </section>
  <footer class="plate-footer">
    <span>DESLIZA →</span>
    <span class="progress">{% for n in range(1, (slide_total|default(1)) + 1) %}<span class="progress-dot{% if n == (slide_index|default(1)) %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 6: Reescribir `plantillas/portada.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <span class="cover-mark"></span>
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index|default(1)) }} / {{ "%02d"|format(slide_total|default(1)) }}</span>
  </header>
  <div class="kicker">{{ tag }}</div>
  <h1 class="title">{{ titulo }}</h1>
  <p class="cover-deck">{{ subtitulo|default(eslogan) }}</p>
  <footer class="plate-footer">
    <span>DESLIZA →</span>
    <span class="progress">{% for n in range(1, (slide_total|default(1)) + 1) %}<span class="progress-dot{% if n == (slide_index|default(1)) %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 7: Reescribir `plantillas/cierre.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index|default(1)) }} / {{ "%02d"|format(slide_total|default(1)) }}</span>
  </header>
  <div class="close-mark">
    <img class="brand-logo" src="{{ logo_uri }}" alt="Data Snake">
    <div class="kicker" style="margin-top:0;">Data Snake</div>
  </div>
  <h2 class="title">GUARDALO<br>PARA TU<br>PRÓXIMO<br>PROYECTO.</h2>
  <p class="close-copy"><strong>@{{ ig_handle }}</strong><br>{{ eslogan }}</p>
  <footer class="plate-footer">
    <span>COMPARTIR →</span>
    <span class="progress">{% for n in range(1, (slide_total|default(1)) + 1) %}<span class="progress-dot{% if n == (slide_index|default(1)) %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 8: Borrar las plantillas viejas**

```bash
git rm plantillas/idea.html plantillas/comparativa.html plantillas/codigo.html
```

- [ ] **Step 9: Run tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_render.py -v`
Expected: PASS (6 tests)

- [ ] **Step 10: Mirar los PNG de verdad (no alcanza con los tests)**

```bash
.venv/Scripts/python.exe -m pytest tests/test_render.py::test_render_cada_plantilla_produce_png -v
```

Ese test escribe en un `tmp_path` que se borra. Para inspeccionar, correr en su lugar:

```bash
.venv/Scripts/python.exe -c "from src.config import get_config; from src.render.renderer import Renderer; from tests.test_render import PLACAS; from pathlib import Path; d=Path('salida/_preview'); [Renderer(get_config()).__enter__().render_placa(p, d/f'{i:02d}.png') for i,p in enumerate(PLACAS,1)]"
```

Abrir `salida/_preview/*.png` y verificar contra `referencia/Captura desde 2026-07-03 16-56-09.png`:
- El título usa Anton (condensado, angosto), no Archivo.
- La portada es verde con texto oscuro.
- La placa `light` es hueso con título violeta y panel oscuro.
- El panel llega bien abajo: no queda un tercio de placa vacío.
- El código se ve en mono dentro de su sección, no en una placa aparte.

Si algo desborda (texto que se sale de los 1350px), ajustar `font-size` de `.title-medium` / `.section-text` en `_estilos.html` y volver a mirar.

- [ ] **Step 11: Commit**

```bash
git add src/config.py src/render/renderer.py plantillas tests/test_render.py
git commit -m "feat: sistema visual denso (Anton, portada verde, placa clara, plantilla unica)"
```

---

### Task 6: El orquestador arma placas densas

**Files:**
- Modify: `src/main.py` (`construir_placas`, `plan_b`, `DRY_RUN`)
- Modify: `tests/test_main.py`

**Interfaces:**
- Consumes: `contenido.normalizar_ideas`, `contenido.ideas_desde_item`, `contenido.KICKER_POR_TIPO` (Tasks 1 y 4); contrato de `contenido.html` (Task 5).
- Produces: `construir_placas(tipo: str, red: dict) -> list[dict]` — `portada` + una placa `contenido` por idea + `cierre`, con `slide_index`/`slide_total` en todas. La placa de contenido cuyo número de idea es múltiplo de 3 sale con `variant: "light"`; el resto, `"dark"`.

- [ ] **Step 1: Write the failing test**

En `tests/test_main.py`, **borrar** `test_construir_placas_tip_incluye_codigo` y `test_construir_placas_uses_code_variant_for_tip_snippet` (la placa `codigo` ya no existe) y agregar:

```python
IDEA = {"titulo": "Excel", "deck": "Limpiar filas",
        "secciones": [{"label": "cuándo conviene", "texto": "Una sola vez."}]}


def test_construir_placas_usa_una_placa_contenido_por_idea():
    red = {"titulo_portada": "EXCEL VS\nPYTHON", "ideas": [IDEA, IDEA]}

    placas = construir_placas("comparativa", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "contenido", "cierre"]
    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}
    assert placas[0]["variant"] == "cover" and placas[-1]["variant"] == "close"


def test_construir_placas_pasa_secciones_y_kicker():
    red = {"titulo_portada": "X", "ideas": [IDEA]}

    placa = construir_placas("comparativa", red)[1]

    assert placa["kicker"] == "opción 01"
    assert placa["deck"] == "Limpiar filas"
    assert placa["secciones"] == IDEA["secciones"]


def test_tercera_idea_sale_en_placa_clara():
    red = {"titulo_portada": "X", "ideas": [IDEA, IDEA, IDEA, IDEA]}

    variants = [p["variant"] for p in construir_placas("rol", red)]

    assert variants == ["cover", "dark", "dark", "light", "dark", "close"]


def test_construir_placas_tip_mete_el_codigo_como_seccion():
    red = {"titulo_portada": "TOP N", "codigo": "SELECT 1;", "lenguaje": "sql",
           "ideas": [{"titulo": "Top N", "texto": "ROW_NUMBER con PARTITION BY."}]}

    placas = construir_placas("tip", red)

    assert [p["plantilla"] for p in placas] == ["portada", "contenido", "cierre"]
    labels = [s["label"] for s in placas[1]["secciones"]]
    assert "el código" in labels


def test_plan_b_tip_arma_ideas_densas():
    item = {"titulo": "Top N en SQL", "gancho": "Top N por grupo.", "codigo": "SELECT 1;",
            "lenguaje": "sql", "explicacion": "ROW_NUMBER numera por grupo."}

    red = main.plan_b("tip", item)

    assert red["plan_b"] is True
    assert [s["label"] for s in red["ideas"][0]["secciones"]] == [
        "el problema", "el código", "por qué funciona"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_main.py -v`
Expected: FAIL — las placas siguen siendo `idea`/`codigo` y no hay `kicker`.

- [ ] **Step 3: Reescribir `construir_placas` en `src/main.py`**

Reemplazar la función entera por:

```python
def construir_placas(tipo: str, red: dict) -> list[dict]:
    tag = {"novedad": "Novedad", "comparativa": "Comparativa",
           "rol": "Carrera en data", "tip": "Tip"}[tipo]
    palabra = contenido.KICKER_POR_TIPO[tipo]

    placas = [{
        "plantilla": "portada",
        "tag": tag,
        "titulo": red["titulo_portada"],
        "subtitulo": red.get("subtitulo", ESLOGAN),
        "variant": "cover",
    }]
    for i, idea in enumerate(contenido.normalizar_ideas(tipo, red), start=1):
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
```

Agregar el import `from src import contenido` y sumar `ESLOGAN` al import de `src.config`.

- [ ] **Step 4: Reescribir `plan_b` en `src/main.py`**

El caption no cambia (sigue armándose desde el item); lo que cambia es que las `ideas` ahora salen de `contenido.ideas_desde_item`:

```python
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
            "codigo": item["codigo"], "lenguaje": item["lenguaje"], "caption": cuerpo}
```

- [ ] **Step 5: Actualizar los fixtures de `--dry-run`**

En `src/main.py`, reemplazar el dict `DRY_RUN` por ideas densas (así el dry-run muestra la placa llena de verdad):

```python
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
```

- [ ] **Step 6: Run tests**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: toda la suite en verde (el test de reel puede salir `skipped` si no hay ffmpeg).

- [ ] **Step 7: Correr el lote de muestra y MIRAR los PNG**

```bash
.venv/Scripts/python.exe -m src.main --dry-run
```

Abrir `salida/semana-<hoy>/01-novedad/*.png`, `02-comparativa/*.png`, `03-rol/*.png`, `04-tip/*.png` y comparar contra `referencia/`. Chequear:
- Ninguna placa tiene un tercio vacío.
- La 3ª idea del `rol` sale en placa clara (hueso + violeta).
- El código del tip se ve dentro del panel, en su sección.
- Ningún texto desborda los 1350px de alto.

Si algo desborda o queda flojo, ajustar `_estilos.html` y volver a correr. **No dar la tarea por terminada sin haber mirado los PNG.**

- [ ] **Step 8: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: el orquestador arma placas densas"
```

---

### Task 7 (Etapa 2): Gemini devuelve deck + secciones

Con la etapa 1 lista, las placas ya son densas en plan B y en `--dry-run`, pero en una corrida real Gemini todavía devuelve `{titulo, texto}` y el puente las degrada a una sola sección. Esta tarea cierra el círculo.

**Files:**
- Modify: `src/redaccion/prompts.py` (los 4 prompts)
- Modify: `src/redaccion/contratos.py`
- Modify: `src/contenido.py` (borrar `normalizar_ideas`)
- Modify: `src/main.py` (`construir_placas` itera `red["ideas"]` directo)
- Modify: `tests/test_contratos.py`, `tests/test_prompts.py`, `tests/test_contenido.py`, `tests/test_main.py`

**Interfaces:**
- Consumes: `SECCIONES_POR_TIPO` (Task 1).
- Produces: contrato JSON de Gemini —
  `{"titulo_portada": str, "ideas": [{"titulo": str, "deck": str, "secciones": [{"label": str, "texto": str}]}], "codigo": str (solo tip), "lenguaje": str (solo tip), "caption": str, "hashtags": [str]}`
  con `label` ∈ `SECCIONES_POR_TIPO[tipo]`.

- [ ] **Step 1: Write the failing test**

En `tests/test_contratos.py`, agregar:

```python
import pytest

from src.redaccion.contratos import validar

_IDEA_OK = {"titulo": "Excel", "deck": "Limpiar filas",
            "secciones": [{"label": "cuándo conviene", "texto": "Una sola vez."},
                          {"label": "dónde duele", "texto": "No queda documentado."}]}


def _red(**extra):
    base = {"titulo_portada": "EXCEL VS PYTHON", "ideas": [_IDEA_OK],
            "caption": "c" * 500, "hashtags": ["data", "sql"]}
    base.update(extra)
    return base


def test_validar_acepta_ideas_densas():
    validar("comparativa", _red())  # no levanta


def test_validar_rechaza_idea_sin_secciones():
    with pytest.raises(ValueError, match="secciones"):
        validar("comparativa", _red(ideas=[{"titulo": "Excel", "deck": "x"}]))


def test_validar_rechaza_label_inventado():
    idea = {"titulo": "Excel", "deck": "x",
            "secciones": [{"label": "lo que se me cantó", "texto": "Una sola vez."}]}
    with pytest.raises(ValueError, match="label"):
        validar("comparativa", _red(ideas=[idea]))
```

Y en `tests/test_prompts.py`, agregar:

```python
def test_prompts_piden_secciones_con_los_labels_fijos():
    from src.contenido import SECCIONES_POR_TIPO
    from src.redaccion import prompts

    p = prompts.prompt_comparativa({
        "tarea": "Limpiar filas", "veredicto": "Depende.",
        "opciones": [{"nombre": "Excel", "cuando_conviene": "Una vez.", "donde_duele": "Manual."}]})

    assert "secciones" in p
    for label in SECCIONES_POR_TIPO["comparativa"]:
        assert label in p
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_contratos.py tests/test_prompts.py -v`
Expected: FAIL — el validador todavía no mira `secciones` y el prompt no las pide.

- [ ] **Step 3: Validador nuevo**

En `src/redaccion/contratos.py`, agregar el import `from src.contenido import SECCIONES_POR_TIPO` y, al final de `validar()`, antes del chequeo de `tip`:

```python
    for i, idea in enumerate(datos["ideas"], start=1):
        if not idea.get("secciones"):
            raise ValueError(f"{tipo}: idea {i} sin secciones")
        permitidos = SECCIONES_POR_TIPO[tipo]
        for seccion in idea["secciones"]:
            if seccion.get("label") not in permitidos:
                raise ValueError(
                    f"{tipo}: idea {i} usa un label fuera del contrato: {seccion.get('label')!r}")
            if not seccion.get("texto", "").strip():
                raise ValueError(f"{tipo}: idea {i} tiene una sección vacía")
```

- [ ] **Step 4: Prompts nuevos**

En `src/redaccion/prompts.py`, agregar arriba (después de `REGLAS_CAPTION`):

```python
REGLAS_IDEAS = """\
Cada "idea" es UNA placa del carrusel y va con: "titulo" (1-3 palabras, entra
gigante), "deck" (una oración que resume la idea) y "secciones". Las secciones
tienen LABELS FIJOS que no podés cambiar ni inventar: usá exactamente los que te
pido, todos, en ese orden. Cada "texto" de sección: 1-2 oraciones, concretas, sin
números inventados."""
```

y cambiar el bloque JSON de cada prompt para que pida secciones con los labels de su tipo. Ejemplo para `prompt_comparativa` (hacer lo análogo en los otros tres, con los labels de `SECCIONES_POR_TIPO`: novedad → `qué cambió` / `por qué importa`; rol → `por qué te la piden` / `cómo la practicás`, una idea por skill; tip → `el problema` / `el código` / `por qué funciona`, y el código va aparte en el campo `codigo`):

```python
def prompt_comparativa(item: dict) -> str:
    opciones = "\n".join(
        f"- {o['nombre']}: conviene si {o['cuando_conviene']} Duele en que {o['donde_duele']}"
        for o in item["opciones"])
    return f"""{VOZ_DE_MARCA}

Material — comparativa para la tarea: "{item['tarea']}".
Opciones:
{opciones}
Veredicto sugerido: {item['veredicto']}

TAREA — Armá un carrusel que enfrente las opciones para esa tarea: portada + UNA
idea por opción. Concreto y honesto, sin fanatismos de herramienta.

{REGLAS_IDEAS}

{REGLAS_CAPTION}

{_CIERRE}
{{
  "titulo_portada": "<MAYÚSCULAS, máximo 3 líneas de 1-3 palabras, con \\n>",
  "ideas": [{{
    "titulo": "<la opción, 1-3 palabras>",
    "deck": "<una oración>",
    "secciones": [
      {{"label": "cuándo conviene", "texto": "<1-2 oraciones>"}},
      {{"label": "dónde duele", "texto": "<1-2 oraciones>"}}
    ]
  }}],
  "caption": "<6-10 oraciones, ~600-900 caracteres>",
  "hashtags": ["<4 a 5>"]
}}"""
```

- [ ] **Step 5: Sacar el puente**

- En `src/contenido.py`: borrar `normalizar_ideas` (ya no hace falta: Gemini valida contra el contrato nuevo y el plan B produce el formato nuevo).
- En `src/main.py:construir_placas`: cambiar `contenido.normalizar_ideas(tipo, red)` por `red["ideas"]`.
- En `tests/test_contenido.py`: borrar los tres tests de `normalizar_*`.
- En `tests/test_main.py`: borrar `test_construir_placas_tip_mete_el_codigo_como_seccion` (ese caso dependía del puente) y verificar que `test_construir_placas_pasa_secciones_y_kicker` siga pasando ideas ya densas.

Ojo: el `tip` ahora necesita que la sección `el código` venga en las ideas. En `src/main.py:construir_placas`, después de armar las placas de contenido, ya no hay que hacer nada especial — el prompt de tip pide la sección `el código` con el snippet, y `plan_b` la arma vía `ideas_desde_item`.

- [ ] **Step 6: Run the whole suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: todo verde.

- [ ] **Step 7: Verificación visual final**

```bash
.venv/Scripts/python.exe -m src.main --dry-run
```

Mirar de nuevo las 4 piezas en `salida/semana-<hoy>/`. Deben verse iguales que al final de la Tarea 6 (el dry-run no pasa por Gemini): si algo se rompió, es que `construir_placas` quedó mal al sacar el puente.

- [ ] **Step 8: Actualizar el manual y commitear**

En `MANUAL-TECNICO.md`: actualizar la tabla de la sección 3 (las plantillas ahora son `portada`, `contenido`, `cierre`; ya no existen `idea`, `comparativa`, `codigo`), y en la sección 7 (knobs) cambiar la fila de diseño visual por `plantillas/*.html` (`portada`, `contenido`, `cierre`, `_estilos`) y agregar una fila: "Labels de las secciones de cada placa → `src/contenido.py` → `SECCIONES_POR_TIPO`". Actualizar la fecha del pie.

```bash
git add src/redaccion/prompts.py src/redaccion/contratos.py src/contenido.py src/main.py tests MANUAL-TECNICO.md
git commit -m "feat: Gemini devuelve deck y secciones (etapa 2)"
```
