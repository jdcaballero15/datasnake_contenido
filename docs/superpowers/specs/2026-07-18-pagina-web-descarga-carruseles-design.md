# Diseño — Página web para bajar carruseles desde el celu

Fecha: 2026-07-18
Estado: aprobado (pendiente de plan de implementación)

## Problema / objetivo

Hoy el lote semanal llega a Google Drive y el dueño de `@data.snake` lo postea a mano
desde el celu. Funciona, pero la experiencia en Drive es engorrosa: hay que navegar
carpetas, bajar imagen por imagen y abrir un `.txt` para copiar el caption.

Se quiere una **página web propia**, pensada para el celu, donde de un vistazo estén los
carruseles de la semana con dos acciones cómodas por pieza: **bajar las placas de ese
carrusel** y **copiar su caption**. Es "semi-automatizado": el sistema arma y publica todo
solo; el humano solo baja, copia y postea.

Drive **no** se elimina: sigue como respaldo (red de seguridad si la página falla).

## Decisiones tomadas (brainstorming 2026-07-18)

| Decisión | Elección |
|---|---|
| ¿Reemplaza a Drive? | **No**, se suma. Drive queda como respaldo. |
| Hosting / acceso | **GitHub Pages público**. Gratis, sin cuentas nuevas, lo publica el mismo workflow. URL poco adivinable; el contenido igual será público en Instagram. |
| Alcance | **Solo la semana actual**. Cada domingo reemplaza a la anterior. El histórico vive en Drive. |
| Bajar imágenes | **Un botón "Bajar todas" POR PIEZA**, que baja solo las placas de ESE carrusel (no un botón global). Vía el menú de compartir del celu → "Guardar imágenes". |
| Copiar caption | Botón "Copiar caption" por pieza, al portapapeles. |

## Arquitectura

**Enfoque elegido: página autocontenida + deploy oficial de GitHub Pages.**

Flujo, sumado al pipeline actual (no lo modifica, se engancha después de generar el lote):

```
src/main.py genera salida/semana-<fecha>/ (crudo: pieza/NN.png + caption.txt + meta.json)
        │
        ▼
src/web/pagina.py:generar_pagina(lote_dir, destino_html)
        │  arma UN index.html autocontenido:
        │   - imágenes embebidas como data URIs (base64) → no se hostean aparte
        │   - captions embebidos
        │   - CSS de marca inline + JS inline (copiar / bajar)
        ▼
.github/workflows/contenido.yml (pasos nuevos, después de "Generar lote"):
   - Generar página → python -m src.web.pagina
   - actions/upload-pages-artifact@v3  (sube la carpeta con index.html)
   - actions/deploy-pages@v4           (publica a GitHub Pages)
```

- **No se commitea ningún PNG ni HTML al repo**: la página se publica como artifact de
  Pages, así el historial de git queda limpio.
- Requiere habilitar Pages en el repo con **source = GitHub Actions** (una vez, a mano en
  Settings → Pages) y agregar los permisos `pages: write` e `id-token: write` al job.
- La página es un solo archivo autocontenido: el mismo artefacto sirve para abrir local
  (`salida/index.html`) y para testear sin publicar.

### Por qué data URIs y no archivos separados

Un lote son ~3 piezas × 3–6 placas × ~60–120 KB ≈ 1–2 MB. Embebido en base64 es un
`index.html` de ~2–3 MB: pesado pero perfectamente servible una vez por semana, y evita
tener que publicar/organizar archivos de imagen aparte. Para el botón "Bajar todas", el JS
decodifica cada data URI a un `Blob`/`File` en memoria (necesario para el menú de compartir).

## Diseño de la página (qué ve el usuario en el celu)

- **Header:** "Data Snake" + "Semana del \<fecha\>". Tema oscuro de marca (mismos colores
  que las placas: `COLOR_FONDO`, `COLOR_ACENTO`, etc. de `src/config.py`).
- **Una sección por pieza** (en el orden del lote: novedad, luego evergreen). Cada sección:
  - Encabezado de la pieza: su tipo (ej. "NOVEDAD") y el título.
  - Las placas del carrusel **en orden**, grandes, apiladas una debajo de otra (stack
    vertical: lo más simple y confiable en el celu). Se ven a tamaño legible.
  - Botón **"📥 Bajar todas"** → baja SOLO las placas de esa pieza.
  - El caption completo en un recuadro monoespaciado/legible + botón **"📋 Copiar caption"**.
- **Responsive, mobile-first.** Ancho máximo tipo columna; las imágenes a `max-width:100%`.

### Interacciones (JS inline)

1. **Copiar caption:** `navigator.clipboard.writeText(caption)`; feedback visual ("¡Copiado!").
   Fallback: seleccionar el texto del recuadro si `clipboard` no está disponible.
2. **Bajar todas (por pieza):**
   - Primario: `navigator.share({ files: [File, File, ...] })` con las placas de esa pieza.
     En iOS/Android abre el menú de compartir; el usuario toca "Guardar imágenes" y las N
     placas caen juntas en Fotos, en orden, listas para Instagram.
   - Se chequea `navigator.canShare({ files })` antes de ofrecerlo.
   - **Fallback** (desktop o navegador sin share de archivos): dispara una descarga por
     imagen con `<a download>` (en desktop no molesta como en el celu).

## Componentes y límites

- `src/web/pagina.py` — **único módulo nuevo**. `generar_pagina(lote_dir: Path, destino:
  Path) -> None`: lee el lote crudo (reusa la misma estructura que `src/exportar.py` ya
  recorre: subcarpetas por pieza con `NN.png`, `caption.txt`, `meta.json`), y escribe un
  `index.html`. Depende solo de la stdlib (base64, pathlib) + una plantilla.
- `plantillas/pagina.html` — plantilla Jinja2 de la página (coherente con las otras
  plantillas del proyecto). Recibe la lista de piezas con sus imágenes (data URIs) y caption.
- **No toca** `src/main.py` salvo, opcionalmente, una línea para generar la página también
  en las corridas locales (útil para previsualizar). La publicación es solo del workflow.

## Testing

- Test de `generar_pagina`: con un lote de prueba (pieza con 2 PNG + caption), verifica que
  el `index.html` resultante contenga: los data URIs de las imágenes, el caption, un botón
  "Bajar todas" por pieza y el botón de copiar. (pytest, sin navegador.)
- Verificación manual end-to-end: correr el workflow, abrir la URL de Pages **desde el
  celu**, y confirmar las tres cosas: se ven las placas, "Bajar todas" guarda en Fotos, y
  "Copiar caption" copia al portapapeles.

## Lo que NO hacemos (YAGNI)

- Sin histórico de semanas (solo la actual).
- Sin login / password (público, ver Decisiones).
- Sin backend ni base de datos: la página es estática y autocontenida.
- Sin botón global "bajar todo el lote": el posteo es un carrusel por vez.
- Sin publicar a Instagram (sigue siendo 100% manual, por diseño del proyecto).
