# Frecuencia diaria + volumen ajustable — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pasar la generación de contenido de semanal a diaria, con un dial `PIEZAS_POR_DIA` (arranca en 1) y una página que muestra los últimos 7 días bajándolos de Drive.

**Architecture:** Tres cambios acoplados: (1) generación diaria — config knob + `plan_dia` novedad-first + carpetas `lote-<fecha>` + seed diario; (2) la página web arma los últimos 7 lotes en vez de uno; (3) el workflow corre a diario y, antes de armar la página, baja de Drive (el archivo histórico) los lotes recientes, porque el runner arranca en limpio.

**Tech Stack:** Python 3.12 (stdlib + Jinja2, ya presentes), pytest, GitHub Actions, rclone.

## Global Constraints

- **Sin dependencias nuevas** (stdlib + Jinja2, ya instaladas).
- **Frecuencia diaria:** cron `"0 11 * * *"` (todos los días 11:00 UTC = 08:00 ARG).
- **Dial de volumen:** `PIEZAS_POR_DIA` en `src/config.py`, default **1**. Novedad-first: 1 novedad si hay una fresca + el resto evergreen rotando sin repetir; nunca un lote vacío.
- **Carpetas `lote-<fecha>`** (antes `semana-<fecha>`). La página lee solo `lote-*`.
- **Página:** los últimos **7** lotes (día más nuevo primero), una sección por día; dentro, las piezas de ese día con sus botones "Bajar todas" / "Copiar caption" (sin cambios en esa parte).
- **Historial entre corridas:** el workflow baja de Drive los lotes de los últimos ~8 días (`rclone copy gdrive: salida/ --max-age 8d`) antes de armar la página.
- **No se toca** el flujo de subida a Drive (sigue con `--exclude "ParaSubir/**"`) ni la autopublicación (sigue 100% manual).
- **Ejecutar tests con:** `.venv/Scripts/python.exe -m pytest` (Windows / Git Bash).

---

### Task 1: Generación diaria — `PIEZAS_POR_DIA`, `plan_dia`, carpetas `lote-`, seed diario

**Files:**
- Modify: `src/config.py`
- Modify: `src/main.py`
- Test: `tests/test_config.py`, `tests/test_main.py`

**Interfaces:**
- Produces:
  - `src.config.PIEZAS_POR_DIA: int` (=1) y `Config.piezas_por_dia: int` (default `PIEZAS_POR_DIA`).
  - `main.plan_dia(cfg: Config, seed: int, novedad: dict | None) -> list[dict]` (reemplaza `plan_semana`; misma forma de salida `[{"tipo","item"}, ...]`).
  - Carpeta del lote: `salida/lote-<YYYY-MM-DD>/`.
- Consumes: `feeds.elegir_novedad(cfg)`, `bancos.seleccionar(cfg, banco, 1, seed)`, `TIPOS` (existentes, sin cambios).

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_config.py`, **reemplazar** la función `test_mix_is_one_novedad_two_evergreen` (líneas 17-21) por:

```python
def test_piezas_por_dia_default_uno():
    cfg = get_config()
    assert config.PIEZAS_POR_DIA == 1
    assert cfg.piezas_por_dia == 1
    assert set(config.TIPOS_EVERGREEN) == {"comparativa", "rol", "tip"}
```

En `tests/test_main.py`, **reemplazar** las tres funciones existentes
`test_plan_semana_sin_novedad_da_tres_evergreen` (líneas 5-10),
`test_plan_semana_con_novedad` (líneas 13-19) y
`test_plan_semana_usa_seeds_deterministas` (líneas 91-104) por:

```python
def test_plan_dia_sin_novedad_un_evergreen(monkeypatch, tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    piezas = main.plan_dia(cfg, seed=202627, novedad=None)
    assert len(piezas) == 1
    assert piezas[0]["tipo"] in cfg.tipos_evergreen


def test_plan_dia_con_novedad_una_pieza_novedad(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    nov = {"id": "http://x/1", "titulo": "T", "resumen": "R", "link": "http://x/1", "fuente": "PBI"}
    piezas = main.plan_dia(cfg, seed=202627, novedad=nov)
    assert len(piezas) == 1
    assert piezas[0]["tipo"] == "novedad"


def test_plan_dia_volumen_mayor_novedad_mas_evergreen(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.piezas_por_dia = 3
    nov = {"id": "http://x/1", "titulo": "T", "resumen": "R", "link": "http://x/1", "fuente": "PBI"}
    piezas = main.plan_dia(cfg, seed=202627, novedad=nov)
    assert len(piezas) == 3
    assert piezas[0]["tipo"] == "novedad"
    assert all(p["tipo"] in cfg.tipos_evergreen for p in piezas[1:])


def test_plan_dia_usa_seeds_deterministas(monkeypatch, tmp_path):
    from src.fuentes import bancos
    cfg = get_config()
    cfg.dir_estado = tmp_path
    cfg.piezas_por_dia = 3
    seeds = []
    real = bancos.seleccionar

    def spy(c, banco, cantidad, seed):
        seeds.append(seed)
        return real(c, banco, cantidad, seed)

    monkeypatch.setattr(main, "seleccionar", spy)
    main.plan_dia(cfg, seed=202627, novedad=None)  # sin novedad → 3 evergreen slots
    assert seeds == [202628, 202629, 202630]  # seed+1, +2, +3 — determinista
```

- [ ] **Step 2: Correr y ver fallar**

Run: `.venv/Scripts/python.exe -m pytest tests/test_config.py tests/test_main.py -q`
Expected: FAIL (`AttributeError: module 'src.config' has no attribute 'PIEZAS_POR_DIA'` y `module 'src.main' has no attribute 'plan_dia'`).

- [ ] **Step 3: Editar `src/config.py`**

Reemplazar el bloque de líneas 21-23:

```python
# Mix semanal: 1 novedad (RSS) + 2 evergreen rotando entre estos tipos.
MIX_NOVEDAD = 1
TIPOS_EVERGREEN = ["comparativa", "rol", "tip"]
```

por:

```python
# Carruseles por corrida (diaria). El "dial" para escalar volumen: subilo para generar
# más por día. OJO: muy arriba, los 45 evergreen se repiten rápido y las novedades RSS
# no dan abasto — habría que sumar feeds/bancos.
PIEZAS_POR_DIA = 1
# Tipos evergreen que rotan cuando no hay (o sobran) novedades.
TIPOS_EVERGREEN = ["comparativa", "rol", "tip"]
```

Y en la dataclass `Config`, reemplazar la línea 51:

```python
    mix: dict = field(default_factory=lambda: {"novedad": MIX_NOVEDAD, "evergreen": 2})
```

por:

```python
    piezas_por_dia: int = PIEZAS_POR_DIA
```

- [ ] **Step 4: Editar `src/main.py` — reemplazar `plan_semana` por `plan_dia`**

Reemplazar la función completa `plan_semana` (líneas 37-53) por:

```python
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
```

- [ ] **Step 5: Editar `src/main.py` — carpeta `lote-` y seed diario en `main()`**

En la función `main()`:

1. Reemplazar la línea 220:
   ```python
       lote_semana = cfg.dir_salida / f"semana-{hoy:%Y-%m-%d}"
   ```
   por:
   ```python
       lote_dia = cfg.dir_salida / f"lote-{hoy:%Y-%m-%d}"
   ```

2. Reemplazar las líneas 227-230:
   ```python
           anio, semana, _ = hoy.isocalendar()
           seed = anio * 100 + semana
           novedad = feeds.elegir_novedad(cfg)
           piezas = plan_semana(cfg, seed, novedad)
   ```
   por:
   ```python
           seed = hoy.toordinal()
           novedad = feeds.elegir_novedad(cfg)
           piezas = plan_dia(cfg, seed, novedad)
   ```

3. Reemplazar TODAS las demás apariciones de `lote_semana` por `lote_dia` en `main()` (líneas 240, 246, 247 y 257). Verificá que no quede ninguna con:
   Run: `grep -n "lote_semana\|plan_semana" src/main.py` → no debe devolver nada.

- [ ] **Step 6: Correr los tests y verlos pasar**

Run: `.venv/Scripts/python.exe -m pytest tests/test_config.py tests/test_main.py -q`
Expected: PASS.

- [ ] **Step 7: Suite completo**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: PASS (nota: `tests/test_pagina.py` sigue verde en esta task porque su fixture usa `semana-`/firma vieja y esta task no toca `pagina.py`; se actualiza en la Task 2). Esperado: 72 passed, 1 skipped.

- [ ] **Step 8: Commit**

```bash
git add src/config.py src/main.py tests/test_config.py tests/test_main.py
git commit -m "feat: generación diaria con dial PIEZAS_POR_DIA y carpetas lote-"
```

---

### Task 2: Página con los últimos 7 días

**Files:**
- Modify: `src/web/pagina.py`
- Modify: `plantillas/pagina.html`
- Test: `tests/test_pagina.py`

**Interfaces:**
- Consumes: carpetas `salida/lote-<fecha>/` (Task 1), `_leer_piezas` (existente, sin cambios).
- Produces:
  - `pagina._lotes_recientes(dir_salida: Path, n: int = 7) -> list[Path]` (reemplaza `_lote_mas_reciente`).
  - `pagina.generar_pagina(dir_salida: Path, destino_dir: Path, n_dias: int = 7) -> Path` (firma nueva: recibe el dir raíz de salida).
  - `python -m src.web.pagina` arma la página con los últimos 7 lotes de `salida/`.

- [ ] **Step 1: Reescribir `tests/test_pagina.py`**

Reemplazar TODO el contenido de `tests/test_pagina.py` por:

```python
import base64
import json
from pathlib import Path

from src.web import pagina


def _crear_lote(parent: Path, fecha: str, tipo: str = "novedad", titulo: str = "ZERO COPY S3") -> Path:
    lote = parent / f"lote-{fecha}"
    pieza = lote / f"01-{tipo}"
    pieza.mkdir(parents=True)
    (pieza / "01.png").write_bytes(b"PNGDATA-UNO")
    (pieza / "02.png").write_bytes(b"PNGDATA-DOS")
    (pieza / "caption.txt").write_text("Mira esta herramienta #data", encoding="utf-8")
    (pieza / "meta.json").write_text(
        json.dumps({"titulo": titulo, "tipo": tipo, "id": "x", "plan_b": False, "fecha": fecha}),
        encoding="utf-8")
    return lote


def test_leer_piezas_arma_data_uris_e_imagenes_ordenadas(tmp_path):
    lote = _crear_lote(tmp_path, "2026-07-19")
    piezas = pagina._leer_piezas(lote)
    assert len(piezas) == 1
    p = piezas[0]
    assert p["tipo"] == "novedad"
    assert p["titulo"] == "ZERO COPY S3"
    assert p["caption"] == "Mira esta herramienta #data"
    assert len(p["imagenes"]) == 2
    esperado = "data:image/png;base64," + base64.b64encode(b"PNGDATA-UNO").decode("ascii")
    assert p["imagenes"][0] == esperado


def test_lotes_recientes_ordena_desc_y_filtra(tmp_path):
    _crear_lote(tmp_path, "2026-07-15")
    _crear_lote(tmp_path, "2026-07-19")
    _crear_lote(tmp_path, "2026-07-17")
    (tmp_path / "semana-2026-07-01").mkdir()  # naming viejo → se ignora
    (tmp_path / "web").mkdir()                # no es un lote
    recientes = pagina._lotes_recientes(tmp_path, n=7)
    assert [p.name for p in recientes] == ["lote-2026-07-19", "lote-2026-07-17", "lote-2026-07-15"]


def test_lotes_recientes_corta_en_n(tmp_path):
    for d in range(10, 20):
        _crear_lote(tmp_path, f"2026-07-{d}")
    recientes = pagina._lotes_recientes(tmp_path, n=7)
    assert len(recientes) == 7
    assert recientes[0].name == "lote-2026-07-19"


def test_generar_pagina_multi_dia(tmp_path):
    _crear_lote(tmp_path, "2026-07-18", tipo="rol", titulo="DATA ENGINEER")
    _crear_lote(tmp_path, "2026-07-19", tipo="novedad", titulo="ZERO COPY S3")
    destino = tmp_path / "web"
    ruta = pagina.generar_pagina(tmp_path, destino, n_dias=7)
    assert ruta == destino / "index.html"
    html = ruta.read_text(encoding="utf-8")
    # dos días, una pieza cada uno → dos botones de cada tipo
    assert html.count("bajarTodas(this)") == 2
    assert html.count("copiarCaption(this)") == 2
    # ambas fechas legibles, el día más nuevo primero
    assert "18/07/2026" in html and "19/07/2026" in html
    assert html.index("19/07/2026") < html.index("18/07/2026")
    # títulos e imágenes embebidas
    assert "ZERO COPY S3" in html and "DATA ENGINEER" in html
    assert base64.b64encode(b"PNGDATA-DOS").decode("ascii") in html
```

- [ ] **Step 2: Correr y ver fallar**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pagina.py -q`
Expected: FAIL (`AttributeError: module has no attribute '_lotes_recientes'`, y firma vieja de `generar_pagina`).

- [ ] **Step 3: Editar `src/web/pagina.py`**

Reemplazar el bloque desde `def generar_pagina(` hasta el final del archivo (líneas 47 en adelante) por:

```python
def _fecha_legible(nombre_lote: str) -> str:
    iso = nombre_lote.replace("lote-", "")
    try:
        y, m, d = iso.split("-")
        return f"{d}/{m}/{y}"
    except ValueError:
        return iso


def _lotes_recientes(dir_salida: Path, n: int = 7) -> list[Path]:
    lotes = sorted((p for p in dir_salida.glob("lote-*") if p.is_dir()),
                   key=lambda p: p.name, reverse=True)
    return lotes[:n]


def generar_pagina(dir_salida: Path, destino_dir: Path, n_dias: int = 7) -> Path:
    """Escribe destino_dir/index.html con los últimos n_dias lotes y devuelve su ruta."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    dias = []
    for lote in _lotes_recientes(dir_salida, n_dias):
        piezas = _leer_piezas(lote)
        if piezas:
            dias.append({"fecha": _fecha_legible(lote.name), "piezas": piezas})
    env = Environment(loader=FileSystemLoader(DIR_PLANTILLAS), autoescape=True)
    html = env.get_template("pagina.html").render(
        dias=dias,
        c={"fondo": COLOR_FONDO, "texto": COLOR_TEXTO, "acento": COLOR_ACENTO,
           "surface": COLOR_SURFACE, "borde": COLOR_BORDE, "texto_sec": COLOR_TEXTO_SEC,
           "grad_a": GRAD_A, "grad_b": GRAD_B},
    )
    destino = destino_dir / "index.html"
    destino.write_text(html, encoding="utf-8")
    log.info("Página generada: %s (%d días)", destino, len(dias))
    return destino


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    salida = RAIZ / "salida"
    generar_pagina(salida, salida / "web")


if __name__ == "__main__":
    main()
```

(La función `_leer_piezas` y el helper `_data_uri` de arriba quedan **sin cambios**.)

- [ ] **Step 4: Editar `plantillas/pagina.html` — agrupar por día**

Reemplazar el header y el loop de piezas. Buscar el bloque:

```html
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
```

y reemplazarlo por:

```html
  <header>
    <div class="marca">Data Snake</div>
    <div class="fecha">Últimos días</div>
  </header>

  {% for dia in dias %}
  <section class="dia">
    <h2 class="dia-fecha">{{ dia.fecha }}</h2>
    {% for pieza in dia.piezas %}
    <section class="pieza">
      <span class="tipo">{{ pieza.tipo }}</span>
      <h3>{{ pieza.titulo }}</h3>
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
  </section>
  {% endfor %}
```

Además, en el bloque `<style>`, agregar estas reglas (después de la regla `.pieza h2 { ... }`, y cambiando ese selector a `h3` ya que el título de pieza ahora es `h3`):

Reemplazar:
```css
  .pieza h2 { font-size: 19px; margin: 10px 0 14px; }
```
por:
```css
  .pieza h3 { font-size: 19px; margin: 10px 0 14px; }
  .dia { margin-bottom: 36px; }
  .dia-fecha {
    font-size: 15px; color: var(--sec); font-weight: 700; letter-spacing: .5px;
    margin: 0 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--borde);
  }
```

(El `<script>` con `bajarTodas`/`copiarCaption` y el resto del CSS quedan **sin cambios**: siguen operando sobre `.pieza`, que ahora vive dentro de `.dia`.)

- [ ] **Step 5: Correr los tests y verlos pasar**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pagina.py -q`
Expected: PASS (4 tests).

- [ ] **Step 6: Verificación real local (si hay lotes)**

Renombrá un lote local de prueba a `lote-*` y generá la página:
```bash
[ -d salida/semana-2026-07-14 ] && cp -r salida/semana-2026-07-14 salida/lote-2026-07-14
.venv/Scripts/python.exe -m src.web.pagina
.venv/Scripts/python.exe -c "html=open('salida/web/index.html',encoding='utf-8').read(); print('dias (dia-fecha):', html.count('dia-fecha')); print('bajarTodas:', html.count('bajarTodas(this)'))"
rm -rf salida/lote-2026-07-14 salida/web
```
Expected: imprime al menos 1 `dia-fecha` y ≥1 `bajarTodas`. (Si no hay lote local, saltear este step.)

- [ ] **Step 7: Suite completo**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: PASS (73 passed, 1 skipped).

- [ ] **Step 8: Commit**

```bash
git add src/web/pagina.py plantillas/pagina.html tests/test_pagina.py
git commit -m "feat: la página muestra los últimos 7 días agrupados por fecha"
```

---

### Task 3: Workflow diario + bajar lotes recientes de Drive

**Files:**
- Modify: `.github/workflows/contenido.yml`

**Interfaces:**
- Consumes: `python -m src.web.pagina` (Task 2), naming `lote-*` (Task 1), y las env vars de rclone ya usadas en "Subir a Drive".
- Produces: corrida diaria que baja los lotes recientes de Drive y publica la página de 7 días.

- [ ] **Step 1: Cambiar el cron a diario**

En `.github/workflows/contenido.yml`, reemplazar:
```yaml
    - cron: "0 11 * * 0"   # domingos 11:00 UTC = 08:00 ARG
```
por:
```yaml
    - cron: "0 11 * * *"   # todos los días 11:00 UTC = 08:00 ARG
```

- [ ] **Step 2: Actualizar el comentario de cabecera (líneas 1)**

Reemplazar la primera línea:
```yaml
# Lote semanal de contenido — domingos 08:00 ARG (11:00 UTC).
```
por:
```yaml
# Lote diario de contenido — todos los días 08:00 ARG (11:00 UTC).
```

- [ ] **Step 3: Agregar el paso "Bajar lotes recientes de Drive"**

Localizar el final del paso `Subir a Drive` (la línea `rclone copy salida/ gdrive: --exclude "ParaSubir/**"`) e insertar, **antes** del paso `Generar página web`, este paso nuevo:

```yaml
      - name: Bajar lotes recientes de Drive
        env:
          RCLONE_CONFIG_GDRIVE_TYPE: drive
          RCLONE_CONFIG_GDRIVE_SCOPE: drive
          RCLONE_CONFIG_GDRIVE_TOKEN: ${{ secrets.GDRIVE_TOKEN }}
          RCLONE_CONFIG_GDRIVE_ROOT_FOLDER_ID: ${{ secrets.GDRIVE_FOLDER_ID }}
        run: |
          export RCLONE_CONFIG_GDRIVE_TOKEN="{${RCLONE_CONFIG_GDRIVE_TOKEN#*\{}"
          # La página muestra los últimos ~7 días, pero el runner arranca en limpio:
          # traemos de Drive (el archivo histórico) los lotes subidos en los últimos 8 días.
          # La página lee solo carpetas lote-*; lo que no matchee se ignora.
          rclone copy gdrive: salida/ --max-age 8d
```

- [ ] **Step 4: Validar el YAML**

Run: `.venv/Scripts/python.exe -c "import yaml; d=yaml.safe_load(open('.github/workflows/contenido.yml', encoding='utf-8')); steps=[s.get('name') or s.get('uses') for s in d['jobs']['generar']['steps']]; print('YAML OK'); print(steps); assert 'Bajar lotes recientes de Drive' in steps; assert d['on']['schedule'][0]['cron']=='0 11 * * *'"`
Expected: `YAML OK`, la lista de pasos con "Bajar lotes recientes de Drive" entre "Subir a Drive" y "Generar página web", sin AssertionError.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/contenido.yml
git commit -m "feat: workflow diario y bajar lotes recientes de Drive para la página de 7 días"
```

- [ ] **Step 6: Verificación end-to-end (manual, la hace el controlador tras mergear)**

1. `gh workflow run contenido.yml --repo jdcaballero15/datasnake_contenido`
2. Esperar `success`. En el log confirmar: el paso "Bajar lotes recientes de Drive" corrió, y "Publicar en Pages" dio la URL.
3. Abrir la URL de Pages: deben verse los últimos días (hoy arriba), cada uno con su carrusel y botones. (Al principio habrá pocos días; se van sumando día a día.)

---

## Notas de verificación (self-review)

- **Cobertura del spec:** frecuencia diaria (Task 3 cron), dial `PIEZAS_POR_DIA` + novedad-first (Task 1 `plan_dia`), carpetas `lote-` + seed diario (Task 1), página de 7 días agrupada por fecha (Task 2 `_lotes_recientes`/`generar_pagina`/template), Drive como historial (Task 3 `--max-age 8d`). Todo mapeado.
- **Consistencia de tipos:** `plan_dia(cfg, seed, novedad) -> list[dict]`; `Config.piezas_por_dia`; `_lotes_recientes(dir_salida, n) -> list[Path]`; `generar_pagina(dir_salida, destino_dir, n_dias) -> Path`. Usadas igual en tests, módulos y `__main__`.
- **Naming:** `lote-` producido en Task 1 (main.py) y consumido en Task 2 (glob `lote-*`) y Task 3 (Drive pull + página). El naming viejo `semana-*` que quede en Drive/salida se ignora (la página solo lee `lote-*`).
- **No romper Drive:** el paso de subida no se toca; el de bajada usa las mismas env vars y es de solo lectura hacia `salida/`.
