from pathlib import Path
from types import SimpleNamespace

import pyomo.environ as pyo
import pytest

from optframework.core.yaml_component import YamlComponentBuilder


class _Builder(YamlComponentBuilder):
    _CONFIG_FILENAME = "model_dummy.yaml"


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "model_dummy.yaml"
    config_path.write_text("key: value\n")

    config = _Builder()._load_config(config_path)

    assert config == {"key": "value"}


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _Builder()._load_config(tmp_path / "missing.yaml")


def test_config_path_joins_config_dir_and_filename(tmp_path: Path) -> None:
    data = SimpleNamespace(config_dir=str(tmp_path))

    assert _Builder()._config_path(data) == tmp_path / "model_dummy.yaml"


def test_require_returns_present_key() -> None:
    assert _Builder()._require({"key": "value"}, "key") == "value"


def test_require_missing_key_raises() -> None:
    with pytest.raises(KeyError):
        _Builder()._require({}, "key")


def test_resolve_source_valid_prefix() -> None:
    data = SimpleNamespace(produtos=["a", "b"])

    assert _Builder()._resolve_source("data.produtos", data) == ["a", "b"]


def test_resolve_source_invalid_prefix_raises() -> None:
    with pytest.raises(ValueError, match="data\\."):
        _Builder()._resolve_source("produtos", SimpleNamespace())


def test_add_component_attaches_new_component() -> None:
    model = pyo.ConcreteModel()

    _Builder()._add_component(model, "PRODUTOS", pyo.Set(initialize=["a"]))

    assert list(model.PRODUTOS) == ["a"]


def test_add_component_existing_without_overwrite_raises() -> None:
    model = pyo.ConcreteModel()
    model.add_component("PRODUTOS", pyo.Set(initialize=["a"]))

    with pytest.raises(ValueError, match="já existe"):
        _Builder()._add_component(model, "PRODUTOS", pyo.Set(initialize=["b"]))


def test_add_component_existing_with_overwrite_replaces() -> None:
    model = pyo.ConcreteModel()
    model.add_component("PRODUTOS", pyo.Set(initialize=["a"]))

    _Builder()._add_component(
        model, "PRODUTOS", pyo.Set(initialize=["b"]), overwrite=True
    )

    assert list(model.PRODUTOS) == ["b"]


def test_import_rule_resolves_class() -> None:
    imported = _Builder()._import_rule(
        "optframework.core.yaml_component.YamlComponentBuilder"
    )

    assert imported is YamlComponentBuilder


def test_import_rule_missing_module_raises() -> None:
    with pytest.raises(ModuleNotFoundError):
        _Builder()._import_rule("nonexistent.module.Rule")
