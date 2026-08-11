import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from optframework.results.result import Result


def result_to_dict(result: Result, solution: dict[str, Any]) -> dict[str, Any]:
    """Monta um dict plano e JSON-safe a partir de Result e da solução extraída."""
    infeasibility = None
    if result.infeasibility is not None:
        infeasibility = asdict(result.infeasibility)
        infeasibility["message"] = result.infeasibility.render()

    sensitivity = None
    if result.sensitivity is not None:
        sensitivity = asdict(result.sensitivity)
        sensitivity["message"] = result.sensitivity.render()

    data = {
        "termination_condition": str(result.termination_condition),
        "is_infeasible": result.is_infeasible,
        "solution": solution,
        "metrics": asdict(result.metrics) if result.metrics is not None else None,
        "infeasibility": infeasibility,
        "sensitivity": sensitivity,
    }
    return _json_safe(data)


def write_result_json(
    result: Result, solution: dict[str, Any], path: str | Path
) -> Path:
    """Grava result_to_dict(...) como JSON (indent=2, UTF-8) em disco e devolve o Path."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(result_to_dict(result, solution), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return target


def _json_safe(obj: object) -> object:
    """Torna chaves de dict recursivamente str — índices de variáveis multidimensionais vêm como tuple."""
    if isinstance(obj, dict):
        return {str(key): _json_safe(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(item) for item in obj]
    return obj
