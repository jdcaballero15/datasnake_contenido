"""Carpeta plana ParaSubir/ + 00-CAPTIONS.txt para subir a mano de una."""

import shutil
from pathlib import Path


def exportar(lote_dir: Path, destino: Path) -> None:
    if not lote_dir.exists():
        return
    destino.mkdir(parents=True, exist_ok=True)
    captions = []
    for pieza in sorted(p for p in lote_dir.iterdir() if p.is_dir()):
        for archivo in sorted(pieza.iterdir()):
            if archivo.suffix in (".png", ".mp4"):
                shutil.copy(archivo, destino / f"{pieza.name}__{archivo.name}")
        cap = pieza / "caption.txt"
        if cap.exists():
            captions.append(f"===== {pieza.name} =====\n{cap.read_text(encoding='utf-8')}\n")
    (destino / "00-CAPTIONS.txt").write_text("\n".join(captions), encoding="utf-8")
