import json

from src.config import get_config


def _banco(nombre):
    ruta = get_config().dir_datos / f"{nombre}.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def test_comparativas_tienen_opciones_ricas():
    items = _banco("comparativas")
    assert len(items) == 15
    for item in items:
        assert item["id"] and item["tarea"] and item["veredicto"]
        assert len(item["opciones"]) >= 2
        for opcion in item["opciones"]:
            assert opcion["nombre"], f"{item['id']}: opción sin nombre"
            assert len(opcion["cuando_conviene"]) >= 30, f"{item['id']}: cuando_conviene pobre"
            assert len(opcion["donde_duele"]) >= 30, f"{item['id']}: donde_duele pobre"
