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
