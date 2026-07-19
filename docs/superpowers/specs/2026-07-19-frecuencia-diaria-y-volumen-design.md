# Diseño — Frecuencia diaria + volumen ajustable

Fecha: 2026-07-19
Estado: aprobado (pendiente de plan de implementación)

## Problema / objetivo

Hoy el sistema genera **1 lote de 3 piezas por semana**. El dueño de `@data.snake` quiere
postear más seguido y por eso necesita **más carruseles distintos por día**. El objetivo es
pasar a **generación diaria**, arrancando en **1 carrusel por día** y con un "dial" para
**subir el volumen progresivamente** sin tocar código cada vez.

El cuello de botella no es el horario sino el **contenido**: cada pieza consume 1 novedad
(RSS) o 1 evergreen (banco local, 45 ideas en total). A 1/día alcanza de sobra (meses); al
escalar habrá que sumar feeds/bancos, pero eso queda fuera de este cambio.

## Decisiones tomadas (brainstorming 2026-07-19)

| Decisión | Elección |
|---|---|
| Frecuencia | **Diaria** (todos los días 08:00 ARG = 11:00 UTC). |
| Volumen | **1 carrusel/día** ahora, vía un dial en config (`PIEZAS_POR_DIA`), subible después. |
| Tipo del carrusel diario | **Novedad si hay una fresca; si no, evergreen** rotando. Con N>1: 1 novedad (si hay) + resto evergreen. |
| Página | Muestra **los últimos ~7 días** (hoy arriba), una sección por día. |
| Historial entre corridas | **Enfoque A: Drive como archivo.** Cada día se bajan de Drive los últimos días para armar la página (el runner arranca en limpio). |
| Naming de carpetas | `lote-<fecha>` (antes `semana-<fecha>`, ya no aplica). |
| Label de la página | La **fecha** de cada día (antes "Semana del…"). |

## Arquitectura

Cambios sobre el pipeline actual (generación + Drive + página en Pages), sin romper nada
de lo que ya anda:

```
CRON diario (0 11 * * *)
   │
   ▼
src/main.py  → genera lote-<fecha>/ con PIEZAS_POR_DIA piezas (novedad-first)
   │            (folder renombrado semana- → lote-; seed diario reproducible)
   ▼
workflow: Subir a Drive          (hoy; igual que ahora, --exclude "ParaSubir/**")
   │
   ▼
workflow: Bajar recientes de Drive   ← PASO NUEVO
   │   rclone copy gdrive: salida/ --max-age 8d
   │   (trae los lote-<fecha> de los últimos ~8 días a salida/; acotado por modtime)
   ▼
src/web/pagina.py → arma index.html con los ÚLTIMOS 7 lote-* presentes en salida/
   │                 (una sección por día; dentro, las piezas de ese día con sus botones)
   ▼
workflow: publicar en GitHub Pages   (igual que ahora)
```

- **Drive** acumula una carpeta por día → es el historial. El paso "Bajar recientes" lo usa
  para reconstruir la página de 7 días en cada corrida (el runner no persiste entre días).
- El download es **acotado**: `--max-age 8d` trae solo lo subido en los últimos ~8 días
  (los ~7-8 lotes recientes), no todo el historial. La página igual corta a 7 por nombre.
- Transición limpia: los lotes viejos de prueba se llaman `semana-*`; la página solo lee
  `lote-*`, así que no aparecen y envejecen solos.

## Componentes y cambios por archivo

### `src/config.py`
- Agregar `PIEZAS_POR_DIA = 1` (el dial). Documentar que subirlo aumenta carruseles/día y
  que, muy arriba, hay que sumar feeds/bancos para no repetir.
- La lógica de mezcla deja de usar el dict `mix`/`MIX_NOVEDAD` (ver `main.py`); si quedan
  sin uso, se eliminan.

### `src/main.py`
- `lote_semana` → `lote_dia = cfg.dir_salida / f"lote-{hoy:%Y-%m-%d}"` (rename de variable y
  del prefijo de carpeta).
- Seed diario reproducible: `seed = hoy.toordinal()` (antes `anio*100+semana`).
- Reemplazar `plan_semana(cfg, seed, novedad)` por `plan_dia(cfg, seed, novedad)`:
  arma `PIEZAS_POR_DIA` piezas → 1 novedad si `novedad` no es None, y el resto
  (`PIEZAS_POR_DIA - novedades`) evergreen rotando por seed sin repetir. Si
  `PIEZAS_POR_DIA == 1` y no hay novedad, sale 1 evergreen. Nunca sale un lote vacío.
- El export a `ParaSubir` (`exportar.exportar`) queda **como está** (sigue sin subirse a
  Drive por el `--exclude`); no es parte de este cambio. (Posible limpieza futura.)

### `src/web/pagina.py`
- `_lote_mas_reciente` → `_lotes_recientes(dir_salida: Path, n: int = 7) -> list[Path]`:
  devuelve las últimas `n` carpetas `lote-*` por nombre (fecha), más nueva primero.
- `generar_pagina(lote_dir, destino)` → `generar_pagina(dir_salida: Path, destino_dir: Path,
  n_dias: int = 7) -> Path`: arma la página con los últimos `n_dias` lotes. Para cada día
  llama a la lectura de piezas existente (`_leer_piezas`) y arma una estructura
  `dias = [{"fecha": <str legible>, "piezas": [...]}, ...]`.
- El ejecutable (`__main__`) pasa a `generar_pagina(RAIZ/"salida", RAIZ/"salida"/"web")`.
- `fecha` legible por día (ej. `19/07/2026`) derivada del nombre `lote-<YYYY-MM-DD>`.

### `plantillas/pagina.html`
- Envolver las secciones de pieza en **grupos por día**: `{% for dia in dias %}` con un
  encabezado de fecha, y adentro `{% for pieza in dia.piezas %}` con la sección de pieza
  actual (placas + "Bajar todas" + caption + "Copiar caption") **sin cambios**.
- El header deja de decir "Semana del <fecha>"; pasa a algo como "Últimos días".

### `.github/workflows/contenido.yml`
- `cron: "0 11 * * 0"` → `cron: "0 11 * * *"` (diario). Actualizar comentarios de cabecera
  (ya no es semanal).
- Paso nuevo **"Bajar lotes recientes de Drive"** entre "Subir a Drive" y "Generar página
  web": mismas env vars de rclone que el paso de subida, corriendo
  `rclone copy gdrive: salida/ --max-age 8d` (con el mismo saneo del token BOM).

## Interfaces (firmas nuevas/cambiadas)

- `plan_dia(cfg: Config, seed: int, novedad: dict | None) -> list[dict]` (reemplaza
  `plan_semana`, misma forma de salida: `[{"tipo", "item"}, ...]`).
- `pagina._lotes_recientes(dir_salida: Path, n: int = 7) -> list[Path]`.
- `pagina.generar_pagina(dir_salida: Path, destino_dir: Path, n_dias: int = 7) -> Path`
  (ahora recibe el dir raíz de salida, no un lote puntual).
- Config nuevo: `PIEZAS_POR_DIA: int` (default 1).

## Testing

- `plan_dia`: con `PIEZAS_POR_DIA=1` y novedad presente → 1 pieza novedad; sin novedad →
  1 pieza evergreen. Con `PIEZAS_POR_DIA=3` y novedad → 1 novedad + 2 evergreen; sin
  novedad → 3 evergreen. Sin repetir tipos evergreen dentro del lote.
- `_lotes_recientes`: con carpetas `lote-2026-07-15..21` + una `semana-*` + `web/` →
  devuelve solo las 7 `lote-*` más nuevas, orden desc, ignora `semana-*` y `web`.
- `generar_pagina` (multi-día): con 2 lotes de 1 pieza cada uno → el HTML tiene 2 grupos de
  día (2 fechas) y 2 botones "Bajar todas" en total; el día más nuevo aparece primero.
- Ajustar los tests existentes que usan el prefijo `semana-` y la firma vieja de
  `generar_pagina` (`tests/test_pagina.py`, `tests/test_main.py`, `tests/test_exportar.py`
  si aplica) al nuevo naming/firma.
- Verificación manual end-to-end: correr el workflow, confirmar en el log que baja los
  lotes recientes y publica, y abrir la URL de Pages: deben verse los últimos días, cada uno
  con su carrusel y sus botones.

## Lo que NO hacemos (YAGNI)

- No sumamos feeds ni ampliamos bancos ahora (el volumen 1/día no lo necesita). Queda para
  cuando se suba `PIEZAS_POR_DIA`.
- No generamos varias novedades por día (RSS da una por corrida hoy); si al escalar se
  quiere más de 1 novedad/día, será otro cambio en `feeds.elegir_novedad`.
- No auto-publicamos a Instagram (sigue 100% manual, por diseño del proyecto).
- No tocamos el flujo de Drive salvo el paso nuevo de descarga; el `ParaSubir` local
  (dead-ish) se deja para una limpieza futura aparte.
- No paginamos ni hacemos histórico más allá de 7 días en la página (el resto vive en Drive).
