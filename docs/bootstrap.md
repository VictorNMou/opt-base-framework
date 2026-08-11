[← Back to README](../README.md)

# Full project bootstrap: the `copier` template

The manual flow (`uv init` + `uv add` + `optframework-new`, see the
[README](../README.md#using-the-framework-in-another-project)) covers both a brand-new project
and adding the framework to an existing optimizer. For a brand-new project specifically, a
[`copier` template](https://copier.readthedocs.io/) living in `copier.yml`/`template/` (in this
same repository — not a separate repo to keep in sync) runs all three steps at once, already
pinned to the right version:

```bash
uvx copier copy --trust gh:VictorNMou/opt-base-framework --vcs-ref v0.6.1 my-project
```

`--trust` is required because the template runs `_tasks` (`uv sync` + `uv run optframework-new`)
after generating the files — only use `--trust` on templates you trust, since the flag does run
shell commands. The template asks for `project_name`, `description` (optional), `problem_name`
(optional — Enter skips this step, letting you run `optframework-new` manually later), and
`framework_ref` (the version to pin in the generated `pyproject.toml`; defaults to the `--vcs-ref`
used above). If `framework_ref` is a semver tag (`vX.Y.Z`), the generated dependency points at
PyPI (`opt-base-framework==X.Y.Z`); any other value (branch, hash) becomes a Git-pinned dependency
on that ref — useful for testing the template from a branch before a tag exists. It generates
`pyproject.toml`, `.gitignore`, `README.md`, and, if `problem_name` was answered,
`problems/<name>/` in full — all of it by running `optframework-new` internally, without
duplicating the scaffold logic.

Being a `copier` template (not `cookiecutter`), it writes `.copier-answers.yml` into the
generated project, which enables `copier update` later — reapplying future changes to the
template (`copier.yml`/`template/` in this repository) onto an already-generated project, which
`cookiecutter` doesn't support.
