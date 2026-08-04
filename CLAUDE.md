# CLAUDE.md

Instruções de projeto para a Claude Code neste repositório. Ver `README.md` para arquitetura,
quickstart e comandos de desenvolvimento — este arquivo cobre convenções de processo.

## Fluxo de branches (obrigatório)

- `main` é protegida. Nunca commitar ou dar push direto nela, e nunca abrir PR direto de uma
  `feat/<nome>` para `main`.
- Toda branch nova nasce a partir de `develop`, nunca de `main` (mesmo quando `main` e `develop`
  estiverem com o mesmo conteúdo no momento).
- `feat/<nome>` (uma branch por feature/mudança) → PR para `develop`.
- `develop` → PR para `main` quando fizer sentido consolidar (ex.: após uma ou mais features
  mergeadas em `develop`).
- Uma branch/PR por assunto — não empacotar mudanças não relacionadas no mesmo PR.
- PRs são abertos com `gh pr create`; merge fica a cargo do usuário/review no GitHub, não é
  feito localmente.

Exemplo de sequência correta:

```bash
git checkout -b feat/nome-da-mudanca develop
# ... commits ...
git push -u origin feat/nome-da-mudanca
gh pr create --base develop --head feat/nome-da-mudanca --title "..." --body "..."
```

## Antes de abrir um PR

- `uv run pytest` (cobertura ~100% em `src/optframework/`)
- `uv run ruff check .`
- `uv run pylint src problems tests`
