# Contributing

How we work in this repo. The tools enforce almost everything; this file explains why, and
covers what can't be automated.

## Language

Everything is in English: code, comments, docstrings, documentation, commit messages, and
issues. The only exception is the report (`report/`), which is written in Spanish.

## Setup

```bash
uv sync                      # .venv with Python 3.14 and all dependencies, dev tools included
uv run pre-commit install    # pre-commit and commit-msg hooks, once per clone
```

The report needs [Tectonic](https://tectonic-typesetting.github.io/) (or any LaTeX
distribution with `latexmk`).

## Workflow

- Push directly to `main`, running `git pull --rebase` first to keep history linear.
- CI runs the same hooks as pre-commit, runs the tests, and builds the report on every push. If
  CI goes red, fix it before moving on.
- Don't skip hooks with `--no-verify`. If a hook gets in the way, discuss it and change the
  configuration for both of us.

## What runs on each commit

| Hook                        | What it does                                                                                                            |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `pre-commit-hooks`          | Trailing whitespace, end of file, LF line endings, valid YAML and TOML, files over 1 MB, conflict markers, private keys |
| `uv-lock`                   | Keeps `uv.lock` in sync with `pyproject.toml`                                                                           |
| `ruff check`, `ruff format` | Python linting with autofix, and formatting                                                                             |
| `basedpyright`              | Type checking                                                                                                           |
| `pyproject-fmt`             | Canonical formatting of `pyproject.toml`                                                                                |
| `prettier`                  | Formatting of Markdown, YAML, and JSON                                                                                  |
| `actionlint`, `zizmor`      | Errors and security issues in the GitHub Actions workflows                                                              |
| `conventional-pre-commit`   | Commit message format                                                                                                   |

Hooks that fix things themselves (formatting, whitespace) stop the commit and leave their changes
in the working tree: review them, `git add`, and commit again.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), with the description in
the imperative mood, lowercase, and without a trailing period:

```text
<type>(<optional scope>): <description>
```

| Type       | Use it for                                                     |
| ---------- | -------------------------------------------------------------- |
| `feat`     | New functionality: environment, agent, metric, training script |
| `fix`      | A bug fix                                                      |
| `docs`     | Report, README, experiment log, and other documentation        |
| `test`     | New or corrected tests                                         |
| `refactor` | Code changes that don't change behavior                        |
| `perf`     | Performance improvements                                       |
| `build`    | Dependencies, `pyproject.toml`, `uv.lock`                      |
| `ci`       | GitHub Actions                                                 |
| `chore`    | Maintenance that fits none of the above, like hooks and config |
| `style`    | Formatting only; rarely needed, since the hooks do it          |
| `revert`   | Reverting an earlier commit                                    |

Suggested scopes, not mandatory: `env`, `agent`, `train`, `eval`, `plots`, `report`, `log`.

```text
feat(env): add proportional transaction costs
fix(train): seed the evaluation environment
docs(report): write the environment specification
build: add stable-baselines3
```

One commit is one logical change. If the description needs an "and", it's probably two commits.
The report's diagnostic case cites specific commits, so each one should make sense on its own.

## Code

- Python 3.14, with type annotations on every signature. basedpyright in `standard` mode.
- Formatting and linting with ruff, 100-character lines.
- Google-style docstrings on everything public.
- Randomness always through a seeded `numpy.random.Generator`, never global state
  (`np.random.seed`): runs must be reproducible.
- Paths with `pathlib`.
- Tests in `tests/` with pytest. They should check properties that matter (for example, that
  without costs the constant Merton policy beats other fractions), not that the code merely
  runs.
- Dependencies with `uv add <package>` or `uv add --dev <package>`; never edit `uv.lock` by
  hand.

## Experiments

- Run from a clean commit, so the hash reproduces the result.
- Each run writes to `runs/YYYY-MM-DD_<description>/`, which isn't versioned.
- Every run that teaches something, failed ones included, goes into
  [`docs/experiment-log.md`](docs/experiment-log.md) with its commit. The report's Development
  section and diagnostic case come from there, and reconstructing it at the end doesn't work.
- Report figures are generated by code into `report/figures/` and are versioned. Prefer vector
  PDF.

## Report

- Written in Spanish.
- One sentence per line in the `.tex` files: diffs show which sentence changed, and conflicts
  between us are rare.
- One section per file in `report/sections/`.
- Citations with `\citet` or `\citep` against `report/references.bib`.
- Up to 10 pages, not counting the AI use declaration, which starts on a new page at the end.
- Run `tectonic report/main.tex` before pushing report changes; CI builds it anyway and uploads
  the PDF as an artifact.

## Tool versions

- Python, ruff, basedpyright, pytest, and pre-commit are pinned in `uv.lock`. The ruff and
  basedpyright hooks use that same version through `uv run`, so the editor, the hook, and CI
  agree.
- The other hooks are pinned in `.pre-commit-config.yaml`.
- GitHub Actions are pinned by commit SHA, with the version in a comment, so nobody can change
  what CI runs by moving a tag.
- To update: `uv lock --upgrade` and `uv run pre-commit autoupdate`, in a separate `build:`
  commit.
