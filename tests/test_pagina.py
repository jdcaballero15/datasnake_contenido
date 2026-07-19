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
    # una sección por pieza, con sus dos botones (contamos el onclick, no la
    # definición de la función, que también contiene "bajarTodas(")
    assert html.count("bajarTodas(this)") == 1
    assert html.count("copiarCaption(this)") == 1


def test_lote_mas_reciente(tmp_path):
    (tmp_path / "semana-2026-07-05").mkdir()
    (tmp_path / "semana-2026-07-19").mkdir()
    (tmp_path / "web").mkdir()  # no debe confundirse con un lote
    assert pagina._lote_mas_reciente(tmp_path).name == "semana-2026-07-19"
