# Diseño — Data Snake Contenido

> Spec de la versión inicial del sistema de contenido automático de **Data Snake**,
> replicando la arquitectura probada de Efecto Sosiego / Efecto Gambeta (presupuesto $0,
> GitHub Actions como cron, Google Drive como depósito) y adaptándola al nicho
> **tech / analítica de datos / carreras en data**.
>
> Fecha: 2026-07-02.

## 1. Objetivo y alcance

Construir una **fábrica de contenido automática con presupuesto $0** para la marca
**Data Snake** (analítica de datos, herramientas y carreras en el mundo data). Cada
semana el sistema:

1. Junta ideas de dos fuentes: **novedades de herramientas** (vía RSS) y **bancos
   evergreen** locales.
2. Redacta los textos con **Gemini** (free tier, con resiliencia a rate-limits y plan B local).
3. Renderiza **carruseles** (placas PNG 1080×1350, tema oscuro de marca).
4. Arma **reels 9:16** opcionales a partir de las placas (slideshow con música).
5. Deja todo **listo en Google Drive** para postear **a mano**.

**Publicación 100% manual** (decisión de diseño, ver §3): el sistema NO autopublica. El
dueño abre Drive, elige el audio en tendencia y sube a Reels / TikTok / Shorts / LinkedIn.

### Fuera de alcance (v1)
- Autopublicación a APIs (Meta / LinkedIn). Se descarta toda la "Parte B" del original.
- Contestador de comentarios.
- Voz en off (TTS). Los reels son texto en pantalla + música.

## 2. Marca

- **Nombre / handle:** Data Snake — Instagram `data.snake`.
- **Eslogan:** *"Herramientas, resultados y carrera en data"* (va en la placa de cierre y en la bio).
- **Tono / voz:** técnico y **orientado a resultados** — muestra lo que la herramienta
  *hace y logra*, no "esto es fácil, arrancá acá". Para alguien que **ya está en tech**.
  Registro: **voseo, cercano y amigable**. Nunca inventa benchmarks, estudios ni estadísticas.
- **Tema visual:** **oscuro** (opuesto al "salvia clara" del original). Logo = serpiente
  line-art cuyo cuerpo forma una línea de tendencia de datos, degradé violeta→verde.

### Paleta (de la guía de marca de Data Snake)
| Slot del sistema | Nombre | HEX |
|---|---|---|
| `COLOR_FONDO` | Midnight (fondo base) | `#111827` |
| `COLOR_TEXTO` | Cloud (texto principal) | `#CBD5E1` |
| `COLOR_ACENTO` | Ocean Blue (primario / CTAs) | `#2A7FA8` |
| `COLOR_BORDE` | Border (bordes / dividers) | `#253347` |
| Superficie de cards | Deep Slate | `#1C2B3A` |
| Texto secundario | Mist | `#7B91A8` |
| Acento gradiente 1 | Slate Violet | `#7C5CBF` |
| Acento gradiente 2 | Lavender (hover) | `#A98BE8` |
| Acento gradiente 3 | verde del logo | (del SVG/PNG del logo) |

La UI base es **azul-forward** (Ocean Blue). El **gradiente violeta→verde** se reserva
para acentos de marca: títulos de portada, la "línea" decorativa, el nodo del logo.

## 3. Arquitectura

Solo la mitad de **generación** del sistema original + la **entrega** a Drive. Sin servidor,
sin base de datos: GitHub Actions es el cron, el repo guarda el estado en JSON, Drive es el
depósito.

```
GitHub Actions (cron semanal)
  1. FUENTE      RSS-first (feedparser) → novedad fresca no vista
                 +  bancos evergreen JSON (rotación por seed, sin repetir)
  2. REDACCIÓN   Gemini con voz Data Snake (resiliencia 429 + modelos de respaldo)
                 → si falla, plan B: texto local a partir del propio item
  3. RENDER      Jinja2 rellena plantillas HTML → Playwright/Chromium screenshot PNG 1080×1350
  4. VIDEO       ffmpeg: placas → reel.mp4 9:16 con música CC0 (opcional por pieza)
  5. ENTREGA     rclone copy salida/ → Google Drive
                 +  carpeta plana "ParaSubir/" con media + 00-CAPTIONS.txt (→ Google Doc)
```

**Por qué manual y no autopublicación:** las plataformas núcleo (Reels/TikTok/Shorts) no
tienen autopublicación práctica en este stack, y postear a mano permite elegir **audio en
tendencia** (lo que da alcance). Descartar la Parte B elimina la mitad más compleja y frágil
del original (tokens de Meta, app review, ventanas horarias, cola de publicación).

### Determinismo / idempotencia
`seed = año*100 + semana_ISO`. Misma semana ⇒ misma selección de contenido. El estado
(`estado/usados.json`, `estado/fuente_vista.json`) evita repetir.

## 4. Modelo de contenido (4 tipos)

| Tipo | Fuente | Banco / feed | Formato de salida |
|---|---|---|---|
| **novedad** | RSS de herramientas | `fuentes/feeds.py` (+ config de feeds) | carrusel |
| **comparativa** | evergreen | `datos/comparativas.json` | carrusel |
| **rol** | evergreen | `datos/roles.json` | carrusel |
| **tip** | evergreen | `datos/tips.json` | carrusel con snippet de código |

- **novedad:** una novedad de herramienta (release/changelog/feature) desarrollada con el
  ángulo Data Snake: *qué salió, qué te permite hacer ahora, cómo se usa*.
- **comparativa:** enfrenta herramientas/enfoques para una tarea concreta
  (ej. "Excel vs Python vs SQL para limpiar 10k filas").
- **rol:** un rol/carrera del mundo data (ej. "Qué hace un Data Analyst: skills, herramientas,
  sueldo, camino").
- **tip:** un truco concreto y accionable, con **snippet de código/fórmula**
  (SQL, Python/pandas, DAX, fórmula de Excel) renderizado con resaltado por CSS.

**Mix semanal:** `{"novedad": 1, "evergreen": 2}`, donde los 2 evergreen rotan entre
comparativa/rol/tip por seed. Si no hay novedad fresca esa semana, el slot de novedad **cae a
evergreen** (plan B: nunca una semana vacía).

## 5. Componentes (unidades y responsabilidades)

| Módulo | Rol | Origen |
|---|---|---|
| `src/config.py` | TODO lo configurable: paleta, mix, eslogan, handle, tiempos de reel, rutas | nuevo (adaptado) |
| `src/fuentes/feeds.py` | Lee feeds RSS/Atom, filtra por frescura, deduplica, elige novedad no vista | **nuevo** |
| `src/fuentes/bancos.py` | Selección + rotación de los bancos evergreen (sin repetir) | copiar del original |
| `src/redaccion/prompts.py` | Voz de marca Data Snake + contrato JSON por tipo | **nuevo** (reescrito) |
| `src/redaccion/gemini.py` | Cliente Gemini: modelos de respaldo, reintentos 429, latch de cupo | copiar tal cual |
| `src/redaccion/contratos.py` | Valida la respuesta de Gemini antes de renderizar | copiar/ajustar |
| `src/render/renderer.py` | Jinja2 → Playwright screenshot PNG | copiar tal cual |
| `src/video/reel.py` | Placas → reel.mp4 con ffmpeg (render atómico) | copiar tal cual |
| `src/audio/musica.py` | Elige música CC0 determinista | copiar tal cual |
| `src/exportar.py` | Carpeta plana "ParaSubir/" + 00-CAPTIONS.txt | copiar/renombrar del original |
| `src/main.py` | Orquesta la corrida | adaptar (sin publicar; con feeds) |
| `plantillas/*.html` | Diseño de placas (tema oscuro) | **nuevo** |
| `datos/*.json` | Bancos evergreen | **nuevo** |
| `.github/workflows/contenido.yml` | Cron + instalación + corrida + entrega a Drive | adaptar (sin publicar.yml) |

**Se elimina del original:** `src/publicar/` completo, `automatizaciones/contestador/`,
`.github/workflows/publicar.yml`, y todos sus secrets de Meta.

## 6. Scraper de novedades (`fuentes/feeds.py`)

- **RSS-first:** lista de feeds RSS/Atom estables (blogs oficiales: Power BI, Tableau,
  AWS Big Data / QuickSight, Anthropic, etc.), leídos con `feedparser`.
- **Filtro de frescura:** solo entradas de los últimos **14 días** (la corrida es semanal;
  ventana de 2 semanas da colchón).
- **Dedup:** `estado/fuente_vista.json` guarda los IDs/links ya usados; se elige la entrada
  más fresca **no vista**.
- **Fallback HTML:** una web sin feed se scrapea por HTML de forma puntual (selector propio);
  si el selector se rompe, esa fuente devuelve vacío y no voltea la corrida.
- **Plan B:** si ninguna fuente da novedad fresca, el slot de novedad se llena con un
  evergreen extra.

## 7. Plantillas (tema oscuro, `plantillas/`)

- `_estilos.html` — CSS común: paleta dark, **fuente mono** para código (ej. JetBrains Mono /
  IBM Plex Mono) + sans geométrica para texto; el gradiente violeta→verde de marca.
- `portada.html` — tapa del carrusel: título con gradiente + logo.
- `idea.html` / `paso.html` — ideas/pasos numerados (comparativa, rol, novedad).
- `codigo.html` — **snippet de código** con resaltado de sintaxis por CSS (tips, novedades).
- `comparativa.html` — formato "vs" / tabla para comparativas.
- `cierre.html` — placa final: CTA + `@data.snake` + eslogan.

El logo se incrusta como data-URI (PNG del ícono sobre fondo oscuro; si más adelante hay SVG,
se cambia por SVG).

## 8. Redacción (`prompts.py`)

- **`VOZ_DE_MARCA`:** Data Snake, voseo cercano y amigable, técnico y orientado a resultados,
  para gente ya en tech; sin "es fácil/arrancá acá"; sin inventar datos/estudios/benchmarks.
- **`REGLAS_CAPTION`:** caption de retención (largo a definir en implementación, ~600–900
  chars como el original), sin CTAs (se agregan aparte), 4–5 hashtags del rubro data/tech.
- Un `prompt_<tipo>(item)` por tipo (novedad/comparativa/rol/tip), cada uno pide un **JSON
  estricto** (`response_mime_type: application/json`) con los campos que consume la plantilla.
- **Plan B** (sin IA): arma un caption decente a partir del propio item y marca `plan_b: true`.

## 9. Caption final (`main.py`)

```
{cuerpo escrito por Gemini}

{CTA_1}
{CTA_2}

#hashtag1 #hashtag2 … (máx 5)
```
CTAs orientadas a la señal del algoritmo (compartir/guardar), redactadas para tech
(ej. "Guardalo para tu próximo proyecto", "Mandáselo a alguien que arranca en data").
Definición exacta de las CTAs en implementación (`config.py`).

## 10. Entrega a Drive

```
DataSnake/                     (carpeta = secret GDRIVE_FOLDER_ID)
├── semana-AAAA-MM-DD/         espejo de salida/ de la corrida
│   ├── 01-novedad/   01.png…, reel.mp4, caption.txt, meta.json
│   ├── 02-comparativa/ …
│   └── 03-<tipo>/ …
└── ParaSubir/
    └── semana-AAAA-MM-DD/   media aplanado + 00-CAPTIONS (Google Doc nativo)
```
`rclone` sin archivo de config (autenticación por variables de entorno). Sin carpeta
`Publicado/` (no hay autopublicación). Si Drive falla, plan B: el lote queda como *artifact*
del run de Actions.

## 11. Secrets y estado

**Secrets (GitHub Actions):**
| Nombre | Para qué |
|---|---|
| `GEMINI_API_KEY` | Escribir los textos |
| `GDRIVE_TOKEN` | OAuth de rclone |
| `GDRIVE_FOLDER_ID` | Carpeta destino en Drive |

**Estado durable (`estado/*.json`, commiteado):**
| Archivo | Contenido | Para qué |
|---|---|---|
| `estado/usados.json` | IDs usados por banco | no repetir evergreen |
| `estado/fuente_vista.json` | links/IDs de novedades ya usadas | no repetir novedades |

## 12. Workflow (`.github/workflows/contenido.yml`)

- **Cron:** semanal (día/hora a confirmar en implementación; formato UTC). También
  `workflow_dispatch` para correr a mano (el primer cron de un workflow nuevo suele no dispararse).
- **Pasos:** checkout → Python 3.12 → `pip install -r requirements.txt` +
  `playwright install chromium` + `apt-get install rclone ffmpeg` → `python -m src.main` →
  `rclone copy salida/ gdrive:` → commit de `estado/*.json`.
- Sin `publicar.yml`.

## 13. Ubicación, tests y docs

- **Ubicación:** `/home/juan-diego/data.snake/proyectos/datasnake_contenido` (repo nuevo,
  aparte de Efecto Sosiego).
- **Tests:** `pytest` sobre la lógica pura (selección de bancos, feeds con fixtures, contratos,
  export, flujo de `main` con mocks, sin red).
- **`--dry-run`:** genera un lote de muestra sin Gemini ni internet.
- **Docs:** `MANUAL-TECNICO.md` propio (resumen vivo) + este spec.

## 14. Dependencias

Python 3.12 · `requests` `feedparser` `jinja2` `playwright` `pytest` · ffmpeg · rclone
(CLI, instalados en el workflow). `edge-tts` NO se incluye en v1 (sin voz).

## 15. Decisiones abiertas para implementación (no bloquean el diseño)
- Día/hora exactos del cron.
- Feeds RSS concretos de arranque (lista inicial de herramientas).
- Largo exacto del caption y texto final de las 2 CTAs.
- Fuentes tipográficas finales (mono + sans).
- Tamaño inicial de los bancos evergreen (arrancar con ~15–20 items por banco).
