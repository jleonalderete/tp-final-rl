# AGENTS.md

Final project for the Reinforcement Learning course at Universidad de San Andrés. An RL agent
splits wealth between a risky asset and a risk-free one: without costs it must recover Merton's
analytical fraction, and with proportional costs it must learn the no-trade band. Assignment:
[`docs/assignment.md`](docs/assignment.md).

The conventions live in [`CONTRIBUTING.md`](CONTRIBUTING.md) and are followed without exception.

## Commands

```bash
uv sync                              # environment
uv run pre-commit run --all-files    # formatting, linting, type checking, and the other hooks
uv run pytest                        # tests
tectonic report/main.tex             # report
```

A change is done when `uv run pre-commit run --all-files` and `uv run pytest` pass.

## Rules

- Everything is in English except the report (`report/`), which is written in Spanish.
- The assignment grades problem formulation and diagnosis, and both members must be able to
  defend everything in the oral exam. For modeling decisions (environment, reward, algorithm,
  hyperparameters), propose the options with their trade-offs before implementing.
- Commits follow Conventional Commits; the `commit-msg` hook validates them.
- Dependencies only through `uv add`; `uv.lock` is never edited by hand.
- Don't version `runs/`, checkpoints, videos, or compiled PDFs.
- Every relevant run is recorded in [`docs/experiment-log.md`](docs/experiment-log.md) with its
  commit.
