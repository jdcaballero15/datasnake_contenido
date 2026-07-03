# Data Snake Visual Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the generated carousel templates so Data Snake uses an editorial/modular visual system with stronger covers, technical content modules, consistent carousel footer, and controlled light/dark/color variation.

**Architecture:** Keep the existing render pipeline (`src.main` → `Renderer` → Jinja templates) and improve the context passed to templates. Add carousel metadata (`slide_index`, `slide_total`, `variant`) in `construir_placas()`, expose defaults from `Renderer`, then replace the template CSS/HTML with the approved Data Snake system. No content-source or Gemini behavior changes.

**Tech Stack:** Python 3.12, pytest, Jinja2 templates, Playwright screenshot renderer.

---

## File Structure

- `src/main.py`
  - Modify `construir_placas()` so every plate knows its 1-based index, total count, and a visual variant (`cover`, `dark`, `light`, `code`, `close`).
- `src/render/renderer.py`
  - Add safe defaults for `slide_index`, `slide_total`, and `variant` so individual template tests can render partial contexts.
- `plantillas/_estilos.html`
  - Replace the current minimal CSS with the new design system: editorial typography, fixed 1080×1350 layout, header/footer, progress dots, modules, terminal/code blocks, and dark/light/brand variants.
- `plantillas/portada.html`
  - Redesign cover plate with brand-color background, large title, kicker, subtitle slot, header/footer.
- `plantillas/idea.html`
  - Redesign standard content plate with section kicker, title, accent rule, text, and technical module.
- `plantillas/comparativa.html`
  - Redesign comparison plate with the same module system and a `cuándo conviene` label.
- `plantillas/codigo.html`
  - Redesign code plate as a terminal/editor block with monospace type and accent rail.
- `plantillas/cierre.html`
  - Redesign close plate as a branded final CTA using logo, slogan, and handle.
- `tests/test_main.py`
  - Add tests for carousel metadata and variant sequencing.
- `tests/test_render.py`
  - Add template-structure tests for footer/progress/module classes and variant classes.

---

### Task 1: Carousel metadata in plate contexts

**Files:**
- Modify: `src/main.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write failing tests for slide metadata and variants**

Append these tests to `tests/test_main.py`:

```python
from src.main import construir_placas


def test_construir_placas_adds_carousel_metadata_to_every_plate():
    red = {
        "titulo_portada": "EXCEL VS\nPYTHON",
        "ideas": [
            {"titulo": "Excel", "texto": "Rápido para algo puntual."},
            {"titulo": "Python", "texto": "Reproducible para procesos repetidos."},
        ],
    }
    placas = construir_placas("comparativa", red)

    assert [p["slide_index"] for p in placas] == [1, 2, 3, 4]
    assert {p["slide_total"] for p in placas} == {4}
    assert placas[0]["variant"] == "cover"
    assert placas[-1]["variant"] == "close"


def test_construir_placas_uses_code_variant_for_tip_snippet():
    red = {
        "titulo_portada": "TOP N\nEN SQL",
        "ideas": [{"titulo": "Cómo", "texto": "ROW_NUMBER con PARTITION BY."}],
        "codigo": "SELECT 1;",
        "lenguaje": "sql",
    }
    placas = construir_placas("tip", red)

    assert [p["plantilla"] for p in placas] == ["portada", "idea", "codigo", "cierre"]
    assert [p["variant"] for p in placas] == ["cover", "dark", "code", "close"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_main.py::test_construir_placas_adds_carousel_metadata_to_every_plate tests/test_main.py::test_construir_placas_uses_code_variant_for_tip_snippet -v
```

Expected: FAIL with `KeyError: 'slide_index'` or `KeyError: 'variant'`.

- [ ] **Step 3: Implement metadata in `construir_placas()`**

Replace `construir_placas()` in `src/main.py` with:

```python
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
```

- [ ] **Step 4: Run targeted tests**

Run:

```bash
python -m pytest tests/test_main.py::test_construir_placas_adds_carousel_metadata_to_every_plate tests/test_main.py::test_construir_placas_uses_code_variant_for_tip_snippet -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: add carousel metadata to plate contexts"
```

---

### Task 2: Renderer defaults and template structure tests

**Files:**
- Modify: `src/render/renderer.py`
- Modify: `tests/test_render.py`

- [ ] **Step 1: Write failing template-structure tests**

Append these tests to `tests/test_render.py`:

```python
def _render_template(name, **extra):
    r = Renderer(get_config())
    ctx = {
        "tag": "Comparativa",
        "titulo": "EXCEL VS\nPYTHON",
        "numero": 1,
        "texto": "Rápido para algo puntual.",
        "lenguaje": "sql",
        "codigo": "SELECT 1;",
        "slide_index": 2,
        "slide_total": 4,
        "variant": "dark",
        "module_label": "qué resuelve",
        "c": {"fondo": "#111827", "texto": "#CBD5E1", "acento": "#2A7FA8",
              "borde": "#253347", "surface": "#1C2B3A", "texto_sec": "#7B91A8",
              "grad_a": "#7C5CBF", "grad_b": "#2EE6A6"},
        "logo_uri": "data:,",
        "ig_handle": "data.snake",
        "eslogan": "Herramientas, resultados y carrera en data",
    }
    ctx.update(extra)
    return r.env.get_template(f"{name}.html").render(**ctx)


def test_templates_include_carousel_shell_and_progress():
    html = _render_template("idea")
    assert 'class="plate variant-dark"' in html
    assert 'class="plate-header"' in html
    assert '02 / 04' in html
    assert 'class="progress-dot active"' in html
    assert "DESLIZA" in html
    assert "GUARDAR" in html


def test_content_templates_use_modules():
    html = _render_template("comparativa", variant="light", module_label="cuándo conviene")
    assert 'class="plate variant-light"' in html
    assert 'class="content-module"' in html
    assert "CUÁNDO CONVIENE" in html


def test_code_template_uses_terminal_block():
    html = _render_template("codigo", variant="code", codigo="SELECT * FROM t WHERE a <> b & c;")
    assert 'class="terminal-block"' in html
    assert 'class="terminal-code"' in html
    assert "&lt;&gt;" in html and "&amp;" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/test_render.py::test_templates_include_carousel_shell_and_progress tests/test_render.py::test_content_templates_use_modules tests/test_render.py::test_code_template_uses_terminal_block -v
```

Expected: FAIL because current templates do not include `plate-header`, `progress-dot`, `content-module`, or `terminal-block`.

- [ ] **Step 3: Add renderer defaults**

In `src/render/renderer.py`, inside `render_placa()` after `contexto = dict(contexto)`, add:

```python
        contexto.setdefault("slide_index", 1)
        contexto.setdefault("slide_total", 1)
        contexto.setdefault("variant", "dark")
        contexto.setdefault("module_label", "qué resuelve")
```

- [ ] **Step 4: Run existing render test**

Run:

```bash
python -m pytest tests/test_render.py::test_render_cada_plantilla_produce_png -v
```

Expected: PASS when Chromium can launch. If sandbox blocks Chromium with `Operation not permitted`, rerun outside the sandbox.

- [ ] **Step 5: Commit**

```bash
git add src/render/renderer.py tests/test_render.py
git commit -m "test: specify redesigned template shell"
```

---

### Task 3: Shared visual system CSS

**Files:**
- Modify: `plantillas/_estilos.html`

- [ ] **Step 1: Replace `_estilos.html`**

Replace `plantillas/_estilos.html` with:

```html
<style>
  @import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=JetBrains+Mono:wght@400;600;700&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:1080px; height:1350px; }
  body {
    width:1080px; height:1350px; overflow:hidden;
    font-family:'Archivo',system-ui,sans-serif;
    letter-spacing:0;
  }
  .plate {
    width:1080px; height:1350px; padding:86px 76px 72px;
    display:flex; flex-direction:column; position:relative; overflow:hidden;
    color:{{ c.texto }};
  }
  .variant-cover { background:{{ c.acento }}; color:#07111D; }
  .variant-dark, .variant-code, .variant-close { background:{{ c.fondo }}; color:{{ c.texto }}; }
  .variant-light { background:#EEF3F6; color:#111827; }
  .variant-cover::after {
    content:""; position:absolute; right:-120px; bottom:210px; width:360px; height:360px;
    border:34px solid rgba(46,230,166,.28); border-radius:50%;
  }
  .plate-header, .plate-footer {
    position:relative; z-index:2; display:flex; justify-content:space-between; align-items:center;
    font-size:30px; font-weight:700; letter-spacing:.02em;
  }
  .plate-header { color:currentColor; opacity:.88; }
  .plate-footer {
    margin-top:auto; font-size:24px; letter-spacing:.16em; text-transform:uppercase;
    font-weight:900; opacity:.92;
  }
  .progress { display:flex; gap:12px; align-items:center; }
  .progress-dot { width:11px; height:11px; border-radius:50%; background:currentColor; opacity:.28; }
  .progress-dot.active { opacity:1; background:{{ c.grad_b }}; }
  .variant-light .progress-dot.active, .variant-cover .progress-dot.active { background:#111827; }
  .kicker {
    position:relative; z-index:2; margin-top:116px; font-size:28px; line-height:1;
    letter-spacing:.18em; text-transform:uppercase; font-weight:900; color:{{ c.grad_b }};
  }
  .variant-cover .kicker, .variant-light .kicker { color:#111827; }
  .variant-code .kicker { color:{{ c.grad_b }}; }
  .title {
    position:relative; z-index:2; margin-top:28px; font-size:104px; line-height:.94;
    font-weight:900; text-transform:uppercase; white-space:pre-line; letter-spacing:0;
  }
  .title-medium { font-size:88px; }
  .accent-rule {
    position:relative; z-index:2; width:112px; height:8px; border-radius:999px;
    background:{{ c.grad_b }}; margin-top:32px;
  }
  .variant-light .accent-rule, .variant-cover .accent-rule { background:#111827; }
  .lede {
    position:relative; z-index:2; margin-top:34px; font-size:42px; line-height:1.22;
    max-width:880px; font-weight:500;
  }
  .lede strong, .module-text strong { color:#fff; font-weight:900; }
  .variant-light .lede strong, .variant-cover .lede strong,
  .variant-light .module-text strong, .variant-cover .module-text strong { color:#111827; }
  .content-module {
    position:relative; z-index:2; margin-top:54px; padding:38px 42px;
    background:{{ c.surface }}; border:2px solid {{ c.borde }}; border-radius:28px;
  }
  .variant-light .content-module { background:#111827; color:{{ c.texto }}; }
  .module-label {
    color:{{ c.grad_b }}; font-size:26px; letter-spacing:.18em; text-transform:uppercase;
    font-weight:900; margin-bottom:22px;
  }
  .module-text { font-size:38px; line-height:1.32; color:{{ c.texto }}; }
  .variant-light .module-text { color:{{ c.texto }}; }
  .terminal-block {
    margin-top:26px; background:#07111D; border:2px solid #102034; border-left:8px solid {{ c.grad_b }};
    border-radius:20px; padding:28px 32px; color:#9FB2C7;
  }
  .terminal-top { display:flex; gap:12px; color:#58708A; font-family:'JetBrains Mono',monospace; font-size:24px; margin-bottom:22px; }
  .terminal-dot { width:16px; height:16px; border-radius:50%; background:#34485F; display:inline-block; }
  .terminal-code {
    font-family:'JetBrains Mono',monospace; font-size:34px; line-height:1.45;
    white-space:pre-wrap; word-break:break-word;
  }
  .brand-logo { width:126px; height:126px; object-fit:contain; }
  .close-mark { display:flex; align-items:center; gap:24px; }
  .close-copy { margin-top:54px; font-size:50px; line-height:1.16; color:{{ c.texto_sec }}; }
  .close-copy strong { color:{{ c.texto }}; }
</style>
```

- [ ] **Step 2: Run structure tests**

Run:

```bash
python -m pytest tests/test_render.py::test_templates_include_carousel_shell_and_progress tests/test_render.py::test_content_templates_use_modules tests/test_render.py::test_code_template_uses_terminal_block -v
```

Expected: still FAIL until template HTML is replaced in Task 4.

- [ ] **Step 3: Commit**

```bash
git add plantillas/_estilos.html
git commit -m "feat: add Data Snake editorial visual system CSS"
```

---

### Task 4: Redesign template HTML

**Files:**
- Modify: `plantillas/portada.html`
- Modify: `plantillas/idea.html`
- Modify: `plantillas/comparativa.html`
- Modify: `plantillas/codigo.html`
- Modify: `plantillas/cierre.html`

- [ ] **Step 1: Replace `plantillas/portada.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index) }} / {{ "%02d"|format(slide_total) }}</span>
  </header>
  <div class="kicker">{{ tag }}</div>
  <h1 class="title">{{ titulo }}</h1>
  <div class="accent-rule"></div>
  <p class="lede">{{ subtitulo|default("Herramientas, resultados y carrera en data") }}</p>
  <footer class="plate-footer">
    <span>DESLIZA →</span>
    <span class="progress">{% for n in range(1, slide_total + 1) %}<span class="progress-dot{% if n == slide_index %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 2: Replace `plantillas/idea.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index) }} / {{ "%02d"|format(slide_total) }}</span>
  </header>
  <div class="kicker">— {{ "%02d"|format(numero) }}</div>
  <h2 class="title title-medium">{{ titulo }}</h2>
  <div class="accent-rule"></div>
  <p class="lede">{{ texto }}</p>
  <section class="content-module">
    <div class="module-label">› {{ module_label|upper }}</div>
    <p class="module-text">{{ texto }}</p>
  </section>
  <footer class="plate-footer">
    <span>DESLIZA →</span>
    <span class="progress">{% for n in range(1, slide_total + 1) %}<span class="progress-dot{% if n == slide_index %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 3: Replace `plantillas/comparativa.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index) }} / {{ "%02d"|format(slide_total) }}</span>
  </header>
  <div class="kicker">— opción {{ "%02d"|format(numero) }}</div>
  <h2 class="title title-medium">{{ titulo }}</h2>
  <div class="accent-rule"></div>
  <section class="content-module">
    <div class="module-label">› {{ module_label|upper }}</div>
    <p class="module-text">{{ texto }}</p>
  </section>
  <footer class="plate-footer">
    <span>DESLIZA →</span>
    <span class="progress">{% for n in range(1, slide_total + 1) %}<span class="progress-dot{% if n == slide_index %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 4: Replace `plantillas/codigo.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index) }} / {{ "%02d"|format(slide_total) }}</span>
  </header>
  <div class="kicker">— {{ lenguaje|upper }}</div>
  <h2 class="title title-medium">SNIPPET<br>LISTO.</h2>
  <div class="accent-rule"></div>
  <section class="terminal-block">
    <div class="terminal-top">
      <span class="terminal-dot"></span><span class="terminal-dot"></span><span class="terminal-dot"></span>
      <span>data.snake · {{ lenguaje|lower }}</span>
    </div>
    <pre class="terminal-code">{{ codigo }}</pre>
  </section>
  <footer class="plate-footer">
    <span>DESLIZA →</span>
    <span class="progress">{% for n in range(1, slide_total + 1) %}<span class="progress-dot{% if n == slide_index %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 5: Replace `plantillas/cierre.html`**

```html
<!doctype html><html><head>{% include "_estilos.html" %}</head><body>
<main class="plate variant-{{ variant }}">
  <header class="plate-header">
    <span>@{{ ig_handle }}</span>
    <span>{{ "%02d"|format(slide_index) }} / {{ "%02d"|format(slide_total) }}</span>
  </header>
  <div class="close-mark">
    <img class="brand-logo" src="{{ logo_uri }}">
    <div class="kicker" style="margin-top:0;">Data Snake</div>
  </div>
  <h2 class="title">GUARDALO<br>PARA TU<br>PRÓXIMO<br>PROYECTO.</h2>
  <div class="accent-rule"></div>
  <p class="close-copy"><strong>@{{ ig_handle }}</strong><br>{{ eslogan }}</p>
  <footer class="plate-footer">
    <span>COMPARTIR →</span>
    <span class="progress">{% for n in range(1, slide_total + 1) %}<span class="progress-dot{% if n == slide_index %} active{% endif %}"></span>{% endfor %}</span>
    <span>GUARDAR ■</span>
  </footer>
</main>
</body></html>
```

- [ ] **Step 6: Run structure tests**

Run:

```bash
python -m pytest tests/test_render.py::test_templates_include_carousel_shell_and_progress tests/test_render.py::test_content_templates_use_modules tests/test_render.py::test_code_template_uses_terminal_block tests/test_render.py::test_codigo_snippet_is_html_escaped -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add plantillas/portada.html plantillas/idea.html plantillas/comparativa.html plantillas/codigo.html plantillas/cierre.html
git commit -m "feat: redesign carousel templates"
```

---

### Task 5: End-to-end verification and visual sample

**Files:**
- Possibly generated only: `salida/`

- [ ] **Step 1: Run the full test suite**

Run:

```bash
python -m pytest -q
```

Expected: `26+ passed`, existing `ffmpeg` skip is acceptable if `ffmpeg` is absent. If Chromium is blocked by sandbox, rerun outside the sandbox.

- [ ] **Step 2: Generate a dry-run sample**

Run:

```bash
python -m src.main --dry-run
```

Expected: command exits 0 and logs `0 fallidas`.

- [ ] **Step 3: Inspect generated PNGs**

Open at least these files:

```text
salida/semana-<today>/01-novedad/01.png
salida/semana-<today>/02-comparativa/02.png
salida/semana-<today>/04-tip/03.png
salida/semana-<today>/04-tip/04.png
```

Expected visual checks:

- Cover has strong brand-color editorial hierarchy.
- Interior dark/light plates include header, progress, footer, and content modules.
- Code plate renders escaped code in a terminal-style block.
- Close plate uses logo, handle, slogan, and final save/share CTA.
- No text overlaps or leaves the 1080×1350 canvas.

- [ ] **Step 4: Run git status**

Run:

```bash
git status --short
```

Expected: only intentional files changed. `referencia/` may remain untracked and must not be committed unless explicitly requested.

- [ ] **Step 5: Final commit if needed**

If any small verification fixes were needed:

```bash
git add <changed-files>
git commit -m "fix: polish redesigned carousel output"
```

If no fixes were needed, no commit is required for this task.

---

## Self-Review

- Spec coverage: plan covers carousel metadata, stronger covers, modular interiors, terminal/code blocks, controlled light/dark/color variation, footer/pagination, render verification, and dry-run review.
- Scope: scraping/content-source changes are excluded, matching the approved rediseño request.
- Placeholder scan: no placeholder steps remain.
- Type consistency: `slide_index`, `slide_total`, `variant`, and `module_label` are introduced in Task 1/2 and consumed consistently by templates in Task 4.
