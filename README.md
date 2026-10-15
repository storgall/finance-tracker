# finance-tracker

Import bank statements from CSV, categorize expenses and show monthly overviews.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```
uv sync                    # install dependencies
uv run finance-tracker     # run the app
```

## Development

```
uv run pytest              # tests with coverage
uv run ruff check --fix    # lint
uv run ruff format         # format
uv run mypy src            # type check
```

## Data & secrets

- Real bank statements go to `data/` (gitignored). Tests use made-up data in `tests/fixtures/`.
- Secrets go to `.env` (gitignored); see `.env.example`.
- The `Read` deny rules in `.claude/settings.json` do not block `Bash(cat …)`, so data protection
  also relies on the rule in the shared `Py\CLAUDE.md`.
