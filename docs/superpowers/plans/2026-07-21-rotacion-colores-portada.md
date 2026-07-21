# Rotación fija de colores en portadas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alternar determinísticamente la primera placa entre verde, violeta, azul y coral.

**Architecture:** La fecha del lote selecciona por módulo una clave de configuración. `construir_placas()` recibe la variante resultante y el renderer expone las cuatro paletas al CSS de Jinja; las placas internas y el cierre no cambian.

**Tech Stack:** Python 3.12, Jinja2, pytest, HTML/CSS.

## Global Constraints

- Ciclo: verde → violeta → azul → coral → verde.
- La misma fecha debe conservar la misma variante.
- Sin estado persistente ni dependencias nuevas.
- Las variantes `dark`, `light` y `close` no cambian.

---

### Task 1: Seleccionar y propagar la variante de portada

**Files:**

- Modify: `src/config.py:20`
- Modify: `src/main.py:31-35,108-129,244`
- Modify: `tests/test_main.py:1-64`

**Interfaces:**

- Produce `variante_portada(fecha: date) -> str` con los valores `cover-green`, `cover-violet`, `cover-blue` o `cover-coral`.
- Extender `construir_placas(tipo: str, red: dict, variante_cover: str = "cover-green") -> list[dict]`.

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date, timedelta

def test_variante_portada_es_estable_y_avanza_en_ciclo():
    inicio = date(2026, 7, 20)
    variantes = [main.variante_portada(inicio + timedelta(days=i)) for i in range(5)]
    assert variantes == ["cover-green", "cover-violet", "cover-blue", "cover-coral", "cover-green"]

def test_construir_placas_usa_la_variante_de_portada_indicada():
    placas = main.construir_placas("tip", {"titulo_portada": "X", "ideas": [IDEA]}, "cover-coral")
    assert placas[0]["variant"] == "cover-coral"
    assert placas[1]["variant"] == "dark"
    assert placas[-1]["variant"] == "close"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_main.py::test_variante_portada_es_estable_y_avanza_en_ciclo tests/test_main.py::test_construir_placas_usa_la_variante_de_portada_indicada -v`

Expected: FAIL because the selector and third parameter do not exist.

- [ ] **Step 3: Write minimal implementation**

Add to `src/config.py`:

```python
PORTADA_VARIANTES = ("green", "violet", "blue", "coral")
COLORES_PORTADA = {
    "green": {"fondo": "#2EE6A6", "texto": "#0B1F1A"},
    "violet": {"fondo": "#A78BFA", "texto": "#17122C"},
    "blue": {"fondo": "#60A5FA", "texto": "#0B1B35"},
    "coral": {"fondo": "#FB7185", "texto": "#311018"},
}
```

In `src/main.py`:

```python
def variante_portada(fecha: date) -> str:
    return f"cover-{PORTADA_VARIANTES[fecha.toordinal() % len(PORTADA_VARIANTES)]}"
```

Change `construir_placas()` to accept `variante_cover="cover-green"` and use `"variant": variante_cover` in its first plate. Calculate `variante_cover = variante_portada(hoy)` in `main()`, add it to `armar_pieza()`, and call `construir_placas(tipo, red, variante_cover)`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_main.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/config.py src/main.py tests/test_main.py; git commit -m "feat: rotar colores de portada por fecha"`

### Task 2: Renderizar las cuatro paletas de portada

**Files:**

- Modify: `src/render/renderer.py:16-18,75-77`
- Modify: `plantillas/_estilos.html:11,36`
- Modify: `tests/test_render.py:6-8,101-103`

**Interfaces:**

- Consume `COLORES_PORTADA` y publícalo como `c.colores_portada` para Jinja.
- Produce `.variant-cover-green`, `.variant-cover-violet`, `.variant-cover-blue` y `.variant-cover-coral`.

- [ ] **Step 1: Write the failing parametrized test**

```python
@pytest.mark.parametrize("variant", ["cover-green", "cover-violet", "cover-blue", "cover-coral"])
def test_portada_usa_cada_variante_de_color(variant):
    html = _render("portada", variant=variant)
    assert f'class="plate variant-{variant}"' in html
```

Add the four-color `colores_portada` mapping to the `C` fixture used by `_render()`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render.py::test_portada_usa_cada_variante_de_color -v`

Expected: FAIL because the current template only defines `.variant-cover`.

- [ ] **Step 3: Write minimal implementation**

Import `COLORES_PORTADA` in `src/render/renderer.py`, then add `"colores_portada": COLORES_PORTADA` to `c`.

Replace the single CSS cover rule in `plantillas/_estilos.html` with:

```html
{% for nombre, color in c.colores_portada.items() %}
  .variant-cover-{{ nombre }} { background:{{ color.fondo }}; color:{{ color.texto }}; }
  .variant-cover-{{ nombre }} .kicker { color:{{ color.texto }}; }
{% endfor %}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_render.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add src/render/renderer.py plantillas/_estilos.html tests/test_render.py; git commit -m "feat: añadir paletas alternadas para portadas"`

### Task 3: Verificación integrada

**Files:**

- Modify: none

- [ ] **Step 1: Run the full suite**

Run: `.venv\Scripts\python.exe -m pytest`

Expected: all tests pass; only the ffmpeg-dependent reel test may be skipped.

- [ ] **Step 2: Check the deterministic cycle**

Run:

```powershell
@'
from datetime import date, timedelta
from src.main import variante_portada
print([variante_portada(date(2026, 7, 20) + timedelta(days=i)) for i in range(5)])
'@ | .venv\Scripts\python.exe -
```

Expected: `['cover-green', 'cover-violet', 'cover-blue', 'cover-coral', 'cover-green']`.

- [ ] **Step 3: Check the worktree**

Run: `git status --short; git diff --check`

Expected: no whitespace errors and only intended files.

## Self-review

- **Spec coverage:** Task 1 covers deterministic selection and preservation of internal variants; Task 2 adds all four visible palettes; Task 3 verifies the cycle and suite.
- **Placeholder scan:** no `TODO` or `TBD` entries.
- **Type consistency:** the `str` returned by `variante_portada()` is consumed by `construir_placas()` and passed to Jinja through the plate context.

