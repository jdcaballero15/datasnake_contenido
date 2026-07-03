import json

from src.config import get_config
from src.fuentes import bancos


def test_banks_load_and_have_unique_ids(tmp_path):
    cfg = get_config()
    for nombre in ("comparativas", "roles", "tips"):
        items = bancos.cargar_banco(cfg, nombre)
        ids = [i["id"] for i in items]
        assert len(ids) == len(set(ids)), f"{nombre} has duplicate ids"
        assert len(items) >= 2


def test_seleccionar_is_deterministic_by_seed(tmp_path, monkeypatch):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    a = bancos.seleccionar(cfg, "roles", 1, seed=202627)
    b = bancos.seleccionar(cfg, "roles", 1, seed=202627)
    assert a == b


def test_registrar_usados_persists(tmp_path):
    cfg = get_config()
    cfg.dir_estado = tmp_path
    bancos.registrar_usados(cfg, "roles", ["r01"])
    assert bancos.cargar_usados(cfg)["roles"] == ["r01"]
