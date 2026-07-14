# Data Snake — Contenido

Fábrica de contenido semanal a **presupuesto $0** para [@data.snake](https://instagram.com/data.snake)
(analítica de datos, herramientas y carreras en el mundo data).

Cada domingo, GitHub Actions genera un lote de 3 piezas (1 novedad de RSS + 2 evergreen),
las redacta con Gemini (voz propia de la marca, con plan B local si Gemini falla), las
renderiza como carruseles PNG 1080×1350 con portada verde de marca, placas de contenido
oscuras con una variante clara cada 3ª placa, arma un reel 9:16 opcional por
pieza, y deja todo en Google Drive listo para subir **a mano**. No hay autopublicación
(sin Meta API): el dueño de la cuenta elige el audio en tendencia y postea manualmente.

Detalle completo de la arquitectura, el flujo y cómo tocar cada parámetro:
ver **[`MANUAL-TECNICO.md`](MANUAL-TECNICO.md)**.

## Correr en local

```bash
pip install -r requirements.txt
python -m playwright install chromium

# Tests (no necesitan red ni credenciales)
pytest

# Lote de muestra, sin red ni GEMINI_API_KEY (textos fijos de ejemplo)
python -m src.main --dry-run

# Corrida real (necesita GEMINI_API_KEY en el entorno)
export GEMINI_API_KEY="..."
python -m src.main
```

El lote queda en `salida/semana-<fecha>/` (piezas por carpeta) y en
`salida/ParaSubir/semana-<fecha>/` (carpeta plana con toda la media +
`00-CAPTIONS.txt`, lista para revisar y subir).

## Producción

La corrida real vive en `.github/workflows/contenido.yml`: se dispara sola cada domingo
(o a mano desde Actions → *Generar contenido Data Snake* → *Run workflow*) y sube el lote
a Google Drive con `rclone`. Secrets y setup: ver `MANUAL-TECNICO.md`.
