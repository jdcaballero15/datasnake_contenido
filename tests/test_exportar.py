from src import exportar


def test_exportar_aplana_y_junta_captions(tmp_path):
    lote = tmp_path / "semana-2026-07-05"
    pieza = lote / "01-novedad"
    pieza.mkdir(parents=True)
    (pieza / "01.png").write_bytes(b"x" * 50)
    (pieza / "caption.txt").write_text("hola", encoding="utf-8")
    destino = tmp_path / "ParaSubir"
    exportar.exportar(lote, destino)
    assert (destino / "01-novedad__01.png").exists()
    assert "hola" in (destino / "00-CAPTIONS.txt").read_text(encoding="utf-8")
