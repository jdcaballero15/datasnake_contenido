# Manual técnico — Data Snake Contenido

Manual vivo del sistema. Es el resumen de **cómo queda todo funcionando**; el detalle
histórico de cada decisión de diseño vive en `docs/superpowers/specs/` y los planes de
implementación en `docs/superpowers/plans/`.

## 1. Resumen de 30 segundos

Cada domingo a las 08:00 ARG, un workflow de GitHub Actions:

1. Junta ideas: **1 novedad** de herramientas (RSS, la más fresca no usada) + **2 evergreen**
   (comparativa / rol / tip, rotando desde bancos JSON locales sin repetir).
2. Las redacta con **Gemini** (free tier) en la voz de marca de Data Snake; si Gemini falla
   dos intentos, cae a un **plan B local** (texto armado a mano desde el propio item, sin IA).
3. Renderiza cada pieza como **carrusel PNG 1080×1350** (Playwright + Chromium sobre
   plantillas Jinja2, tema oscuro de marca). **Solo carruseles**: el reel de slideshow
   está apagado (`REEL_ACTIVADO = False`), ver §VIDEO.
4. Exporta todo a una carpeta plana `ParaSubir/` con `00-CAPTIONS.txt`, y sube el lote
   entero a **Google Drive** con `rclone`.
5. Commitea el estado (`estado/*.json`) para no repetir contenido la próxima semana.

**Publicación 100% manual**: no hay autopublicación ni API de Meta. El dueño de
`@data.snake` abre la carpeta en la app de Drive del teléfono y sube el carrusel a mano.
No existe un workflow "publicar" — solo este, de generación + entrega.

**Si falta un secret, la corrida falla a propósito** (paso *Chequear secrets*): antes
seguía en verde con textos de plan B y sin subir nada a Drive, y nadie se enteraba.

## 2. Flujo de generación

```
FUENTE      src/fuentes/feeds.py   → elegir_novedad(): RSS-first (feedparser),
                                      la entrada más fresca (FRESCURA_DIAS) no vista
                                      (dedup en estado/fuente_vista.json)
            src/fuentes/bancos.py → seleccionar(): banco evergreen JSON, rotación
                                      reproducible por seed, sin repetir
                                      (estado/usados.json); banco agotado → resetea
                                      la rotación sola.

PLAN        src/main.py:plan_semana() → arma la lista de piezas de la semana:
                                      1 novedad (si hay) + 2 evergreen; si no hay
                                      novedad, ese slot cae a evergreen extra
                                      (nunca sale una semana vacía).

REDACCIÓN   src/redaccion/prompts.py  → un prompt por tipo con la voz de marca
                                      (VOZ_DE_MARCA) + contrato JSON pedido.
            src/redaccion/gemini.py  → llama a Gemini (resiliente a rate-limit).
            src/redaccion/contratos.py → validar(): valida campos, largo de
                                      caption, cantidad de hashtags/ideas.
            → si Gemini falla 2 intentos o no valida: src/main.py:plan_b()
              arma el texto localmente a partir del propio item (sin IA).

RENDER      src/render/renderer.py  → Renderer, un solo Chromium por lote;
                                      render_placa(contexto, destino) por placa,
                                      Jinja2 rellena plantillas/*.html con la
                                      paleta y el logo.

VIDEO       src/video/reel_slideshow.py → generar_reel(carpeta, cfg, seed):
                                      APAGADO (cfg.reel_activado = False): devuelve
                                      None sin hacer nada. Para revivirlo: poner
                                      REEL_ACTIVADO = True en src/config.py y volver
                                      a instalar ffmpeg en el workflow (el comando
                                      de ffmpeg estaba fallando con exit 254: hay
                                      que depurarlo antes de confiar en él).
                                      Encadena las placas PNG con ffmpeg + música
                                      (src/audio/musica.py); si falta ffmpeg o no
                                      hay placas, la pieza sale sin reel y la
                                      corrida no se cae.

EXPORT      src/exportar.py         → exportar(): aplana el lote a
                                      salida/ParaSubir/semana-<fecha>/ con toda
                                      la media + 00-CAPTIONS.txt (captions de
                                      todas las piezas concatenados).

ENTREGA     .github/workflows/contenido.yml → rclone copy salida/ → Drive
                                      (00-CAPTIONS.txt aparte, como Google Doc).
```

Orquestador de todo el flujo: `src/main.py:main()` (`python -m src.main` /
`python -m src.main --dry-run`).

## 3. Los 4 tipos de pieza

| Tipo | Fuente | Banco/feed | Plantillas usadas |
|---|---|---|---|
| `novedad` | RSS (herramientas del mundo data) | `datos/feeds.json` | `portada`, `contenido` × N, `cierre` |
| `comparativa` | Banco evergreen | `datos/comparativas.json` | `portada`, `contenido` × N, `cierre` |
| `rol` | Banco evergreen | `datos/roles.json` | `portada`, `contenido` × N, `cierre` |
| `tip` | Banco evergreen | `datos/tips.json` | `portada`, `contenido` (con el código en una de sus secciones), `cierre` |

Mix semanal: `MIX_NOVEDAD = 1` + 2 evergreen rotando entre `TIPOS_EVERGREEN =
["comparativa", "rol", "tip"]` (ver `src/config.py`). Si no hay novedad fresca disponible
esa semana, el slot se rellena con un evergreen extra — la semana nunca sale vacía.

Cada placa de `contenido` es una "idea" densa: `titulo` + `deck` + `secciones` con
labels fijos por tipo (`src/contenido.py:SECCIONES_POR_TIPO`). La unidad de idea
depende del tipo: novedad → un cambio de la herramienta, comparativa → una opción,
rol → una skill, tip → el tip entero (acá "el código" es una sección más, con el
snippet real en vez de texto).

Plantillas HTML (tema oscuro, Playwright las renderiza a PNG 1080×1350):
`plantillas/portada.html`, `contenido.html`, `cierre.html`, más
`plantillas/_estilos.html` (estilos compartidos, no es una placa en sí).

## 4. Estado y bancos

- `estado/usados.json` — `{banco: [ids ya usados]}`. Se seedea en `{}`. Lo actualiza
  `src/fuentes/bancos.py:registrar_usados()` al final de cada corrida real (no en
  `--dry-run`). Si un banco se agota (menos libres que los pedidos), la rotación de
  ese banco se resetea sola.
- `estado/fuente_vista.json` — lista de ids de entradas RSS ya usadas. Se seedea en `[]`.
  La actualiza `src/fuentes/feeds.py:registrar_vista()`.
- Ambos son commiteados por el propio workflow al final de cada corrida ("Commitear
  estado"), así el estado persiste entre corridas semanales sin base de datos.
- Bancos evergreen (`datos/comparativas.json`, `datos/roles.json`, `datos/tips.json`):
  listas de items con `id` único cada uno; agregar contenido nuevo es agregar entradas
  con `id` nuevo a estos archivos.
- Feeds RSS (`datos/feeds.json`): lista de `{"nombre", "url"}`. Un feed roto no voltea
  la corrida (se ignora esa fuente esa semana).

## 5. Entrega a Google Drive

El workflow sube `salida/` completo a Drive con `rclone` configurado por variables de
entorno (sin archivo de config): `RCLONE_CONFIG_GDRIVE_TYPE`, `RCLONE_CONFIG_GDRIVE_SCOPE`,
`RCLONE_CONFIG_GDRIVE_TOKEN` (desde el secret `GDRIVE_TOKEN`) y
`RCLONE_CONFIG_GDRIVE_ROOT_FOLDER_ID` (desde el secret `GDRIVE_FOLDER_ID`).

`00-CAPTIONS.txt` se sube aparte, importado como Google Doc nativo
(`--drive-import-formats txt --drive-export-formats txt`), para poder leerlo cómodo
desde el celu sin descargar un `.txt`.

Si el paso de Drive falla, el workflow no corta la corrida: el lote igual queda como
**artifact de GitHub Actions** (`lote`, 14 días de retención) para rescatarlo a mano.

No existe workflow de publicación (`publicar.yml` no existe en este repo): la
publicación es manual, fuera de este sistema.

## 6. Secrets y setup en GitHub

Settings → Secrets and variables → Actions. Solo 3 secrets, ninguno más:

| Secret | Qué es |
|---|---|
| `GEMINI_API_KEY` | API key de [aistudio.google.com](https://aistudio.google.com) (free tier) |
| `GDRIVE_TOKEN` | JSON que imprime `rclone authorize "drive"` — token OAuth de la cuenta dueña de la carpeta de Drive (las service accounts no tienen cuota de almacenamiento en Drives personales) |
| `GDRIVE_FOLDER_ID` | ID de la carpeta destino en Drive (lo que sigue a `/folders/` en la URL) |

El primer cron de un workflow recién creado no se dispara solo en GitHub Actions: la
primera corrida hay que lanzarla a mano (Actions → *Generar contenido Data Snake* →
*Run workflow*). De ahí en más el cron corre semana a semana sin intervención.

## 7. Cómo cambiar cada cosa (tabla de knobs)

| Qué querés cambiar | Dónde |
|---|---|
| Día/hora de la corrida semanal | `.github/workflows/contenido.yml` → `cron: "0 11 * * 0"` (UTC) |
| Mix de piezas (cuántas novedades / evergreen, qué tipos evergreen rotan) | `src/config.py` → `MIX_NOVEDAD`, `TIPOS_EVERGREEN` |
| Tono / voz de la marca en los textos | `src/redaccion/prompts.py` → `VOZ_DE_MARCA` (y `REGLAS_CAPTION` para el formato del caption) |
| Paleta de colores de las placas | `src/config.py` → `COLOR_FONDO`, `COLOR_TEXTO`, `COLOR_ACENTO`, `COLOR_BORDE`, `COLOR_SURFACE`, `COLOR_TEXTO_SEC`, `GRAD_A`, `GRAD_B` |
| Eslogan / handle de Instagram / CTAs fijos del caption | `src/config.py` → `ESLOGAN`, `Config.ig_handle`, `CTA_COMPARTIR`, `CTA_GUARDAR` |
| Hashtags de respaldo (cuando Gemini no da los suyos / plan B) | `src/config.py` → `HASHTAGS_DEFAULT` |
| Feeds RSS de novedades (agregar/sacar fuentes) | `datos/feeds.json` |
| Ventana de "novedad fresca" (cuántos días atrás cuenta como actualidad) | `src/config.py` → `FRESCURA_DIAS` |
| Contenido evergreen (comparativas, roles, tips) | `datos/comparativas.json`, `datos/roles.json`, `datos/tips.json` (agregar entradas con `id` nuevo) |
| Diseño visual de las placas | `plantillas/*.html` (`portada`, `contenido`, `cierre`, `_estilos`) |
| Labels de las secciones de cada placa | `src/contenido.py` → `SECCIONES_POR_TIPO` |
| Prender/apagar el reel (hoy apagado) y duración de cada placa | `src/config.py` → `REEL_ACTIVADO`, `SEGUNDOS_POR_SLIDE` |
| Pausa entre llamadas a Gemini (anti rate-limit) | `src/config.py` → `Config.pausa_entre_llamadas` |

## 8. Tests

```bash
pytest
```

Cubre config, bancos, feeds, prompts/contratos, render, reel (slideshow), exportar y el
orquestador (`main`, con `--dry-run` incluido). El test que arma un mp4 de verdad se
saltea (`skip`) si `ffmpeg` no está instalado; el resto verifica que con el reel apagado
no se genere ningún video.

---
Última actualización: 2026-07-14.
