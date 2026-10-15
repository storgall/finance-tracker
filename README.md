# finance-tracker

A small command-line tool that reads a **Moneta** bank statement (XML export), sorts every
transaction into a category using your own keyword rules, and prints a monthly overview of
income and expenses.

- No runtime dependencies, only the Python standard library.
- Money is handled as `Decimal`, never `float`.
- Fully typed (`mypy`), linted and formatted (`ruff`), 100 % test coverage (`pytest`).

## Example

```
$ finance-tracker import tests/fixtures/sample_statement.xml --rules tests/fixtures/rules.toml
Imported 4 transactions
Date range: 2026-09-03 to 2026-09-21

Total Income: 25000.00
Total Expenses: 12225.49
Net Total: 12774.51

Income:
  Uncategorized: 25000.00

Expenses:
  Rent: 12000.00
  Groceries: 125.50
  Streaming: 99.99
```

The sample statement in `tests/fixtures/` is made up. Categories are listed biggest first;
transactions that match no rule end up in `Uncategorized`.

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (it installs the pinned Python 3.13 for you).

```
uv sync
cp rules.example.toml data/rules.toml      # then edit it: your own keywords
uv run finance-tracker import data/statement.xml
```

Use `--rules path/to/rules.toml` to read the rules from another place.
If something is wrong (missing file, broken XML, invalid rules), the error goes to `stderr`
and the exit code is `1`.

### Getting the statement

Moneta's internet banking can export account movements in several formats (PDF, XML, MMB,
ABO). Choose **XML** and save the file to `data/`.

### Rules file

Rules live in a TOML file. One line is one category with a list of keywords:

```toml
[rules]
Groceries = ["albert", "billa", "market"]
Rent = ["nájem"]
Streaming = ["netflix", "spotify"]
```

- A keyword matches when it appears in the transaction's counterparty or description.
- Letter case is ignored.
- **The first matching line wins**, so put more specific rules above general ones.
- Empty and whitespace-only keywords are ignored.

## How it works

```
Moneta XML ──parser──▶ list[Transaction] ──categorizer──▶ Overview ──CLI──▶ text report
                                  ▲
                      rules.toml ─┴─ rules (category → keywords)
```

| Module | Responsibility |
| --- | --- |
| `parser.py` | Reads the XML into `Transaction` objects; raises `ValueError` on malformed data |
| `rules.py` | Loads and validates the TOML rules |
| `categorizer.py` | Assigns a category to each transaction and builds the `Overview` |
| `models.py` | `Transaction` (immutable) and `Overview` (income and expenses per category) |
| `__init__.py` | Command-line interface (`argparse`) and report printing |

## Privacy

Real statements and rules stay in `data/`, which is gitignored. Tests use only made-up data
from `tests/fixtures/`.

## Development

```
uv sync
uv run pytest              # tests with coverage
uv run ruff check --fix    # lint
uv run ruff format         # format
uv run mypy src            # type check
```

GitHub Actions runs `ruff`, `mypy` and `pytest` on every push and pull request.

## Limitations (v0.1)

- Only the Moneta XML format.
- One statement file per run; the overview covers that whole file (Moneta exports are monthly).
- Categories come from keyword rules only; there is no learning and no manual editing of single transactions.

See [docs/ROADMAP.md](docs/ROADMAP.md) for progress.
