# Página web para bajar carruseles — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar cada semana una página web estática (GitHub Pages) con los carruseles del lote, donde desde el celu se bajan las placas de cada pieza y se copia su caption.

**Architecture:** Un módulo nuevo (`src/web/pagina.py`) lee el lote crudo (`salida/semana-<fecha>/`) y arma un único `index.html` autocontenido (imágenes como data URIs, CSS y JS inline). El workflow, después de generar el lote, corre ese módulo y publica la carpeta resultante con las acciones oficiales de GitHub Pages. Drive sigue como respaldo; nada de esto lo toca.

**Tech Stack:** Python 3.12 (stdlib: `base64`, `json`, `pathlib`), Jinja2 (ya es dependencia), GitHub Actions (`configure-pages`, `upload-pages-artifact`, `deploy-pages`), JS del navegador (`navigator.share`, `navigator.clipboard`).

## Global Constraints

- **Sin dependencias nuevas.** `src/web/pagina.py` usa solo stdlib + Jinja2 (ya instalada).
- **Página autocontenida:** imágenes embebidas como data URIs base64; CSS y JS **inline**. No se referencian archivos externos ni se hostean PNGs aparte.
- **Descarga por pieza, nunca global:** cada carrusel tiene su propio botón "Bajar todas" que baja SOLO sus placas.
- **Mobile-first:** la página se diseña para el celu (columna angosta, imágenes `max-width:100%`).
- **Solo la semana actual.** Sin histórico, sin login, sin backend.
- **Colores de marca** desde `src/config.py` (`COLOR_FONDO="#111827"`, `COLOR_TEXTO="#CBD5E1"`, `COLOR_ACENTO="#2A7FA8"`, `COLOR_SURFACE="#1C2B3A"`, `COLOR_BORDE="#253347"`, `COLOR_TEXTO_SEC="#7B91A8"`, `GRAD_A="#7C5CBF"`, `GRAD_B="#2EE6A6"`).
- **Estructura del lote** (la produce `src/main.py:armar_pieza`): `salida/semana-<fecha>/{NN}-{tipo}/` con `{NN}.png` (01.png, 02.png…), `caption.txt`, `meta.json` (`{"titulo","tipo","id","plan_b","fecha"}`). Las piezas se ordenan por nombre de carpeta.
- **Ejecutar tests con:** `.venv/Scripts/python.exe -m pytest` (Windows).

---

### Task 1: Módulo `src/web/pagina.py` + plantilla `plantillas/pagina.html`

Genera un `index.html` autocontenido a partir de un directorio de lote. Es el corazón de la feature; se testea sin navegador.

**Files:**
- Create: `src/web/__init__.py` (vacío)
- Create: `src/web/pagina.py`
- Create: `plantillas/pagina.html`
- Test: `tests/test_pagina.py`

**Interfaces:**
- Consumes: la estructura del lote descrita en Global Constraints (subcarpetas `{NN}-{tipo}` con `{NN}.png`, `caption.txt`, `meta.json`).
- Produces:
  - `generar_pagina(lote_dir: Path, destino_dir: Path) -> Path` — crea `destino_dir` si no existe, escribe `destino_dir/index.html` y devuelve esa ruta.
  - `_leer_piezas(lote_dir: Path) -> list[dict]` — lista de piezas ordenadas; cada una `{"tipo": str, "titulo": str, "caption": str, "imagenes": list[str]}` donde `imagenes` son data URIs.
  - `_lote_mas_reciente(dir_salida: Path) -> Path | None` — devuelve la subcarpeta `semana-*` más reciente por nombre, o `None`.
  - Ejecutable: `python -m src.web.pagina` arma la página del lote más reciente de `salida/` en `salida/web/index.html`.

- [ ] **Step 1: Crear el paquete**

Crear `src/web/__init__.py` vacío:

```python
```

- [ ] **Step 2: Escribir el test que falla**

Crear `tests/test_pagina.py`:

```python
import base64
import json
from pathlib import Path

from src.web import pagina


def _lote_de_prueba(tmp_path: Path) -> Path:
    lote = tmp_path / "semana-2026-07-19"
    pieza = lote / "01-novedad"
    pieza.mkdir(parents=True)
    (pieza / "01.png").write_bytes(b"PNGDATA-UNO")
    (pieza / "02.png").write_bytes(b"PNGDATA-DOS")
    (pieza / "caption.txt").write_text("Mirá esta herramienta #data", encoding="utf-8")
    (pieza / "meta.json").write_text(
        json.dumps({"titulo": "ZERO COPY S3", "tipo": "novedad", "id": "x",
                    "plan_b": False, "fecha": "2026-07-19"}),
        encoding="utf-8")
    return lote


def test_leer_piezas_ordena_y_arma_data_uris(tmp_path):
    lote = _lote_de_prueba(tmp_path)
    piezas = pagina._leer_piezas(lote)
    assert len(piezas) == 1
    p = piezas[0]
    assert p["tipo"] == "novedad"
    assert p["titulo"] == "ZERO COPY S3"
    assert p["caption"] == "Mirá esta herramienta #data"
    assert len(p["imagenes"]) == 2
    esperado = "data:image/png;base64," + base64.b64encode(b"PNGDATA-UNO").decode("ascii")
    assert p["imagenes"][0] == esperado


def test_generar_pagina_escribe_html_autocontenido(tmp_path):
    lote = _lote_de_prueba(tmp_path)
    destino = tmp_path / "web"
    ruta = pagina.generar_pagina(lote, destino)
    assert ruta == destino / "index.html"
    html = ruta.read_text(encoding="utf-8")
    # imágenes embebidas
    assert "data:image/png;base64," in html
    assert base64.b64encode(b"PNGDATA-DOS").decode("ascii") in html
    # caption y título presentes
    assert "Mirá esta herramienta #data" in html
    assert "ZERO COPY S3" in html
    # una sección por pieza, con sus dos botones
    assert html.count("bajarTodas(") == 1
    assert html.count("copiarCaption(") == 1


def test_lote_mas_reciente(tmp_path):
    (tmp_path / "semana-2026-07-05").mkdir()
    (tmp_path / "semana-2026-07-19").mkdir()
    (tmp_path / "web").mkdir()  # no debe confundirse con un lote
    assert pagina._lote_mas_reciente(tmp_path).name == "semana-2026-07-19"
```

- [ ] **Step 3: Correr el test y verlo fallar**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pagina.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'src.web.pagina'` (o `AttributeError`).

- [ ] **Step 4: Escribir la plantilla `plantillas/pagina.html`**

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Snake — {{ fecha }}</title>
<style>
  :root {
    --fondo: {{ c.fondo }}; --texto: {{ c.texto }}; --acento: {{ c.acento }};
    --surface: {{ c.surface }}; --borde: {{ c.borde }}; --sec: {{ c.texto_sec }};
    --grad_a: {{ c.grad_a }}; --grad_b: {{ c.grad_b }};
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--fondo); color: var(--texto);
    font-family: -apple-system, system-ui, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
  }
  .wrap { max-width: 560px; margin: 0 auto; padding: 20px 16px 60px; }
  header { text-align: center; margin-bottom: 28px; }
  header .marca {
    font-weight: 800; font-size: 26px;
    background: linear-gradient(90deg, var(--grad_a), var(--grad_b));
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  header .fecha { color: var(--sec); font-size: 14px; margin-top: 4px; }
  .pieza {
    background: var(--surface); border: 1px solid var(--borde);
    border-radius: 14px; padding: 16px; margin-bottom: 28px;
  }
  .pieza .tipo {
    display: inline-block; font-size: 12px; letter-spacing: 1px; font-weight: 700;
    color: var(--fondo); background: var(--grad_b); padding: 3px 9px; border-radius: 6px;
    text-transform: uppercase;
  }
  .pieza h2 { font-size: 19px; margin: 10px 0 14px; }
  .placas img.placa {
    width: 100%; max-width: 100%; height: auto; display: block;
    border-radius: 10px; margin-bottom: 10px; border: 1px solid var(--borde);
  }
  .acciones { display: flex; gap: 10px; margin: 14px 0; flex-wrap: wrap; }
  button {
    flex: 1 1 140px; cursor: pointer; font-size: 15px; font-weight: 600;
    padding: 12px 14px; border-radius: 10px; border: 1px solid var(--borde);
    background: var(--acento); color: #fff;
  }
  button.sec { background: transparent; color: var(--texto); }
  .caption {
    white-space: pre-wrap; word-break: break-word; font-size: 14px;
    background: var(--fondo); border: 1px solid var(--borde); border-radius: 10px;
    padding: 12px; margin-top: 8px;
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="marca">Data Snake</div>
    <div class="fecha">Semana del {{ fecha }}</div>
  </header>

  {% for pieza in piezas %}
  <section class="pieza">
    <span class="tipo">{{ pieza.tipo }}</span>
    <h2>{{ pieza.titulo }}</h2>
    <div class="placas">
      {% for img in pieza.imagenes %}
      <img class="placa" src="{{ img }}" alt="placa {{ loop.index }}">
      {% endfor %}
    </div>
    <div class="acciones">
      <button onclick="bajarTodas(this)">📥 Bajar todas</button>
      <button class="sec" onclick="copiarCaption(this)">📋 Copiar caption</button>
    </div>
    <div class="caption">{{ pieza.caption }}</div>
  </section>
  {% endfor %}
</div>

<script>
async function bajarTodas(btn) {
  const sec = btn.closest('.pieza');
  const imgs = [...sec.querySelectorAll('img.placa')];
  const files = await Promise.all(imgs.map(async (img, i) => {
    const blob = await (await fetch(img.src)).blob();
    const nombre = 'placa-' + String(i + 1).padStart(2, '0') + '.png';
    return new File([blob], nombre, { type: 'image/png' });
  }));
  if (navigator.canShare && navigator.canShare({ files })) {
    try { await navigator.share({ files }); } catch (e) { /* cancelado por el usuario */ }
  } else {
    // Fallback (desktop / sin share de archivos): descarga individual.
    for (const f of files) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(f); a.download = f.name; a.click();
      URL.revokeObjectURL(a.href);
    }
  }
}
async function copiarCaption(btn) {
  const txt = btn.closest('.pieza').querySelector('.caption').textContent;
  const original = btn.textContent;
  try {
    await navigator.clipboard.writeText(txt);
    btn.textContent = '¡Copiado!';
    setTimeout(() => { btn.textContent = original; }, 1500);
  } catch (e) {
    // Fallback: seleccionar el texto para copiar a mano.
    const sel = window.getSelection(); const rango = document.createRange();
    rango.selectNodeContents(btn.closest('.pieza').querySelector('.caption'));
    sel.removeAllRanges(); sel.addRange(rango);
  }
}
</script>
</body>
</html>
```

- [ ] **Step 5: Escribir `src/web/pagina.py`**

```python
"""Arma una página web estática (un solo index.html autocontenido) con los
carruseles del lote, para bajarlos y copiar el caption desde el celu.

Autocontenida: imágenes embebidas como data URIs, CSS y JS inline. No hostea
archivos aparte. La publica el workflow en GitHub Pages (ver contenido.yml).
"""

import base64
import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.config import (COLOR_ACENTO, COLOR_BORDE, COLOR_FONDO, COLOR_SURFACE,
                        COLOR_TEXTO, COLOR_TEXTO_SEC, GRAD_A, GRAD_B, RAIZ)

log = logging.getLogger("sosiego.web")

DIR_PLANTILLAS = RAIZ / "plantillas"


def _data_uri(ruta: Path) -> str:
    b64 = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _leer_piezas(lote_dir: Path) -> list[dict]:
    piezas = []
    for carpeta in sorted(p for p in lote_dir.iterdir() if p.is_dir()):
        meta = {}
        meta_json = carpeta / "meta.json"
        if meta_json.exists():
            meta = json.loads(meta_json.read_text(encoding="utf-8"))
        cap = carpeta / "caption.txt"
        caption = cap.read_text(encoding="utf-8") if cap.exists() else ""
        imagenes = [_data_uri(png) for png in sorted(carpeta.glob("*.png"))]
        piezas.append({
            "tipo": meta.get("tipo") or carpeta.name.split("-", 1)[-1],
            "titulo": meta.get("titulo", ""),
            "caption": caption,
            "imagenes": imagenes,
        })
    return piezas


def generar_pagina(lote_dir: Path, destino_dir: Path) -> Path:
    """Escribe destino_dir/index.html con el lote y devuelve su ruta."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(DIR_PLANTILLAS), autoescape=True)
    fecha = lote_dir.name.replace("semana-", "")
    html = env.get_template("pagina.html").render(
        piezas=_leer_piezas(lote_dir),
        fecha=fecha,
        c={"fondo": COLOR_FONDO, "texto": COLOR_TEXTO, "acento": COLOR_ACENTO,
           "surface": COLOR_SURFACE, "borde": COLOR_BORDE, "texto_sec": COLOR_TEXTO_SEC,
           "grad_a": GRAD_A, "grad_b": GRAD_B},
    )
    destino = destino_dir / "index.html"
    destino.write_text(html, encoding="utf-8")
    log.info("Página generada: %s (%d piezas)", destino, len(_leer_piezas(lote_dir)))
    return destino


def _lote_mas_reciente(dir_salida: Path) -> Path | None:
    lotes = sorted(p for p in dir_salida.glob("semana-*") if p.is_dir())
    return lotes[-1] if lotes else None


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    salida = RAIZ / "salida"
    lote = _lote_mas_reciente(salida)
    if lote is None:
        log.warning("No hay lote en %s: no se genera página", salida)
        return
    generar_pagina(lote, salida / "web")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Correr los tests y verlos pasar**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pagina.py -v`
Expected: PASS (3 tests: `test_leer_piezas_ordena_y_arma_data_uris`, `test_generar_pagina_escribe_html_autocontenido`, `test_lote_mas_reciente`).

- [ ] **Step 7: Correr el suite completo (no romper nada)**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: PASS (los 68 previos + 3 nuevos = 71 passed, 1 skipped).

- [ ] **Step 8: Commit**

```bash
git add src/web/__init__.py src/web/pagina.py plantillas/pagina.html tests/test_pagina.py
git commit -m "feat: página web autocontenida para bajar carruseles y copiar caption"
```

---

### Task 2: Publicar la página en GitHub Pages desde el workflow

Engancha la generación y publicación de la página al workflow semanal, sin tocar la generación del lote ni la subida a Drive.

**Files:**
- Modify: `.github/workflows/contenido.yml`

**Interfaces:**
- Consumes: `python -m src.web.pagina` (Task 1), que lee el lote de `salida/` y escribe `salida/web/index.html`.
- Produces: la página publicada en la URL de GitHub Pages del repo tras cada corrida.

**Prerrequisito manual (una sola vez, lo hace el dueño del repo):**
En GitHub → repo `jdcaballero15/datasnake_contenido` → **Settings → Pages → Build and deployment → Source = "GitHub Actions"**. Sin esto, el paso `deploy-pages` falla.

- [ ] **Step 1: Ampliar los permisos del job**

En `.github/workflows/contenido.yml`, reemplazar el bloque `permissions` del job `generar` (hoy `contents: write`) y agregar el `environment`. Buscar:

```yaml
  generar:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
```

Reemplazar por:

```yaml
  generar:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
```

- [ ] **Step 2: Agregar los pasos de página + Pages después de "Subir a Drive"**

En el mismo archivo, localizar el final del paso `Subir a Drive` (termina en la línea del `rclone copy ... --exclude "ParaSubir/**"`) y, **antes** del paso `Guardar lote como artifact (respaldo)`, insertar:

```yaml
      - name: Generar página web
        run: python -m src.web.pagina

      - name: Configurar Pages
        uses: actions/configure-pages@v5

      - name: Subir artifact de Pages
        uses: actions/upload-pages-artifact@v3
        with:
          path: salida/web

      - name: Publicar en Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: Validar la sintaxis YAML localmente**

Run: `.venv/Scripts/python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/contenido.yml', encoding='utf-8')); print('YAML OK')"`
Expected: imprime `YAML OK` sin excepción.

- [ ] **Step 4: Commit y push**

```bash
git add .github/workflows/contenido.yml
git commit -m "feat: publicar la página del lote en GitHub Pages desde el workflow"
git pull --rebase origin main
git push origin main
```

(El `pull --rebase` es porque el propio workflow commitea `estado/*.json` a `main` al final de cada corrida; si corrió desde la última vez, tu push sería rechazado sin rebase.)

- [ ] **Step 5: Verificación end-to-end (manual, con evidencia)**

1. Confirmar el prerrequisito manual (Settings → Pages → Source = GitHub Actions).
2. Lanzar la corrida: `gh workflow run contenido.yml --repo jdcaballero15/datasnake_contenido`
3. Esperar a que termine en `success` y que el paso "Publicar en Pages" muestre la `page_url`:
   `gh run view <id> --repo jdcaballero15/datasnake_contenido --log | grep -i "page_url\|deploy"`
4. **Abrir la URL desde el celu** y confirmar las tres cosas del spec:
   - Se ven las placas de cada pieza en orden.
   - "Bajar todas" abre el menú de compartir y "Guardar imágenes" deja las placas de ESA pieza en Fotos.
   - "Copiar caption" copia el caption al portapapeles.

---

## Notas de verificación (self-review)

- **Cobertura del spec:** página autocontenida con data URIs (Task 1, template + `_data_uri`), una sección por pieza con "Bajar todas" propio (template + `bajarTodas`), copiar caption (`copiarCaption`), tema de marca (colores de config), mobile-first (CSS `max-width:560px`), publicación por el workflow a Pages sumada a Drive (Task 2), solo semana actual (`_lote_mas_reciente`), sin login/backend. Todo mapeado.
- **Consistencia de tipos:** `generar_pagina(lote_dir, destino_dir) -> Path` y `_leer_piezas(...) -> list[dict]` con claves `tipo/titulo/caption/imagenes` se usan igual en test, módulo y plantilla.
- **Fallbacks:** `bajarTodas` cae a descarga individual si no hay `navigator.share` de archivos (desktop); `copiarCaption` selecciona el texto si no hay `clipboard`. `_leer_piezas` tolera `meta.json`/`caption.txt` ausentes.
