"""
`optframework-new` — gera `problems/<nome>/` num projeto que já depende do framework.

Substitui o fluxo de "clone o repo do framework e copie problems/exemplo_knapsack/ à mão" —
que quebra o histórico git do projeto consumidor (commits iriam pro remote do framework) — por
um scaffold gerado localmente, depois que o projeto já declarou `opt-base-framework` como
dependência (`uv add "opt-base-framework @ git+https://github.com/VictorNMou/opt-base-framework.git@vX.Y.Z"`).

Uso:

    optframework-new <nome> [--dest problems] [--force]

Gera `<dest>/<nome>/` com `config/` (os 5 YAMLs obrigatórios), `data_loader.py`, `rules.py` e
`run.py` — o mesmo layout descrito no README em "Como criar um problema novo", com um
placeholder trivial (`minimize sum(x)`) que já roda de ponta a ponta, pronto pra ser
substituído pelo problema real.
"""

import argparse
import keyword
import re
import sys
from pathlib import Path

from optframework.scaffold import templates

_NOME_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def _validate_nome(nome: str) -> str:
    """Confere que `nome` vira um módulo Python válido (`problems.<nome>...`)."""
    if not _NOME_RE.match(nome) or keyword.iskeyword(nome):
        raise ValueError(
            f"nome inválido: {nome!r}. Use snake_case (ex.: 'roteirizacao_frota'), "
            "começando com letra minúscula, sem acentos/espaços/hífens."
        )
    return nome


def _to_pascal_case(nome: str) -> str:
    """`roteirizacao_frota` -> `RoteirizacaoFrota`, usado nos nomes das classes de Rules."""
    return "".join(part.capitalize() for part in nome.split("_"))


def _dotted_path(dest: Path, nome: str) -> str:
    """Caminho de import Python correspondente a `<dest>/<nome>` (ex.: `problems.<nome>`)."""
    return ".".join((*dest.parts, nome))


def scaffold_problem(nome: str, dest: Path, *, force: bool = False) -> Path:
    """
    Gera `<dest>/<nome>/` e devolve o Path criado. Levanta se já existir e `force=False`.

    A checagem de sobrescrita é só no nível do diretório — se `problem_dir` já existe e não
    está vazio sem `force=True`, nada é escrito; do contrário, todo arquivo é (re)escrito.
    """
    _validate_nome(nome)
    if dest.is_absolute():
        raise ValueError(
            f"--dest deve ser relativo à raiz do projeto (recebido {dest!r}) — o caminho "
            "vira o prefixo do import Python (ex.: 'problems' -> 'problems.<nome>')."
        )
    problem_dir = dest / nome
    if problem_dir.exists() and not force and any(problem_dir.iterdir()):
        raise FileExistsError(
            f"{problem_dir} já existe e não está vazio (use --force para sobrescrever)."
        )

    class_prefix = _to_pascal_case(nome)
    package_path = _dotted_path(dest, nome)
    rules_module = f"{package_path}.rules"

    config_dir = problem_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    for part in (dest, problem_dir):
        init_file = part / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

    files = {
        config_dir / "model_sets.yaml": templates.MODEL_SETS_YAML,
        config_dir / "model_parameters.yaml": templates.MODEL_PARAMETERS_YAML,
        config_dir / "model_variables.yaml": templates.MODEL_VARIABLES_YAML,
        config_dir / "model_constraints.yaml": templates.render_model_constraints(
            f"{rules_module}.{class_prefix}Rules"
        ),
        config_dir / "model_objective.yaml": templates.render_model_objective(
            f"{rules_module}.{class_prefix}Objectives"
        ),
        problem_dir / "data_loader.py": templates.render_data_loader(class_prefix),
        problem_dir / "rules.py": templates.render_rules(class_prefix),
        problem_dir / "run.py": templates.render_run(package_path, nome),
    }
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")

    return problem_dir


def main(argv: list[str] | None = None) -> int:
    """Entry point de `optframework-new` — parse de args, scaffold e mensagem de próximos passos."""
    parser = argparse.ArgumentParser(
        prog="optframework-new",
        description="Gera a estrutura de um problema novo (problems/<nome>/) sem copiar "
        "código do framework.",
    )
    parser.add_argument(
        "nome", help="nome do problema, em snake_case (ex.: roteirizacao_frota)"
    )
    parser.add_argument(
        "--dest",
        default="problems",
        help="pasta raiz onde o problema é criado (default: problems)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="sobrescreve arquivos existentes, se houver",
    )
    args = parser.parse_args(argv)

    try:
        problem_dir = scaffold_problem(args.nome, Path(args.dest), force=args.force)
    except (ValueError, FileExistsError) as exc:
        print(f"optframework-new: {exc}", file=sys.stderr)
        return 1

    package_path = _dotted_path(Path(args.dest), args.nome)
    print(f"Criado {problem_dir}/")
    print()
    print("Próximos passos:")
    print(f"  1. Edite {problem_dir}/data_loader.py com os dados reais do problema.")
    print(
        f"  2. Declare Sets/Parameters/Variables/Constraints/Objective em {problem_dir}/config/."
    )
    print(f"  3. Implemente os métodos correspondentes em {problem_dir}/rules.py.")
    print(f"  4. uv run python -m {package_path}.run")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
