# finance-tracker

[![CI](https://github.com/storgall/finance-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/storgall/finance-tracker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small command-line tool that reads **Moneta** bank statements (XML export), sorts every
transaction into a category using your own keyword rules, and prints an overview of income and
expenses, for the whole import or split by year, quarter, month, week or day.

- Reads several statements or whole folders at once; overlapping exports are merged and
  duplicate transactions are dropped.
- Categories come from a simple TOML file with your own keywords.
- Transactions you do not want to count (for example transfers to a savings account) can be
  ignored.
- The overview can be exported to CSV or JSON.
- No runtime dependencies, only the Python standard library.
- Money is handled as `Decimal`, never `float`.
- Fully typed (`mypy`), linted and formatted (`ruff`), 100 % test coverage (`pytest`).

## Examples

The statements in `tests/fixtures/` are made up.

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

Categories are listed biggest first; transactions that match no rule end up in
`Uncategorized`.

Several files at once, split by month (the two statements overlap, so one transaction is
skipped as a duplicate):

```
$ finance-tracker import tests/fixtures/sample_statement.xml tests/fixtures/sample_statement_2.xml \
    --rules tests/fixtures/rules.toml --by month
Imported 5 transactions
Skipped 1 duplicate transactions
Date range: 2026-09-03 to 2026-10-02

== 2026-09 ==
Total Income: 25000.00
Total Expenses: 12225.49
Net Total: 12774.51

Income:
  Uncategorized: 25000.00

Expenses:
  Rent: 12000.00
  Groceries: 125.50
  Streaming: 99.99

== 2026-10 ==
Total Income: 0.00
Total Expenses: 50.00
Net Total: -50.00

Income:

Expenses:
  Uncategorized: 50.00
```

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (it installs the pinned Python 3.13 for you).

```
uv sync
cp rules.example.toml data/rules.toml      # then edit it: your own keywords
uv run finance-tracker import data/statements/ --by month --export data/overview.csv
```

### Getting the statements

Moneta's internet banking can export account movements in several formats (PDF, XML, MMB,
ABO). Choose **XML** and save the files to `data/`.

### Usage

```
finance-tracker import PATH [PATH ...] [--rules FILE] [-r] [--by PERIOD] [--export FILE]
finance-tracker --version
```

| Option | Meaning |
| --- | --- |
| `PATH` | One or more statement files and/or folders. A folder is replaced by its `.xml` files, sorted by name. Files and folders can be mixed. |
| `--rules FILE` | The rules file. Default: `data/rules.toml`. |
| `-r`, `--recursive` | Also search the subfolders of the given folders. |
| `--by PERIOD` | Split the overview by `year`, `quarter`, `month`, `week` or `day`. Without it you get one overview for the whole import. Weeks follow ISO 8601. |
| `--export FILE` | Also write the overview to a new `.csv` or `.json` file (see below). |

If something is wrong (missing file, broken XML, invalid rules, a folder without XML files, an
export file that already exists), the error goes to `stderr`, nothing is printed to `stdout`
and the exit code is `1`.

### Rules file

Rules live in a TOML file. One line is one category with a list of keywords:

```toml
[rules]
Groceries = ["albert", "billa", "market"]
Rent = ["nájem"]
Streaming = ["netflix", "spotify"]

[ignore]
keywords = ["123456789/0600"]   # e.g. the number of your savings account
```

- A keyword matches when it appears in the transaction's counterparty or description.
- Letter case is ignored.
- **The first matching line wins**, so put more specific rules above general ones.
- Empty and whitespace-only keywords are ignored.
- The optional `[ignore]` keywords work the same way, but a matching transaction is left out
  of the overview completely; the number of ignored transactions is printed.

### Export

`--export` creates the file and picks the format from its extension (`.csv` or `.json`, any
letter case). **An existing file is never overwritten.** Amounts are written with two decimals;
expenses are positive numbers, as in the printed report.

CSV, one row per period and category (without `--by` the period is called `all`):

```
period,kind,category,amount
all,income,Uncategorized,25000.00
all,expense,Rent,12000.00
all,expense,Groceries,125.50
all,expense,Streaming,99.99
```

JSON, amounts as **strings** so that no precision is lost:

```json
{
  "imported": 4,
  "skipped": 0,
  "ignored": 0,
  "periods": [
    {
      "period": "all",
      "income": {"Uncategorized": "25000.00"},
      "expenses": {"Rent": "12000.00", "Groceries": "125.50", "Streaming": "99.99"},
      "total_income": "25000.00",
      "total_expenses": "12225.49",
      "net_total": "12774.51"
    }
  ]
}
```

(The real file is indented one key per line.)

## How it works

```
Moneta XML files ──files──▶ parser ──▶ merge ──▶ ignore ──▶ categorizer ──▶ Overview
  (or folders)                                                  ▲               │
                                      rules.toml ───────────────┘               ├─▶ text report
                                                              periods ──────────┘   (--by)
                                                                                └─▶ CSV / JSON (--export)
```

| Module | Responsibility |
| --- | --- |
| `files.py` | Expands the given paths: a folder becomes its XML files |
| `parser.py` | Reads the XML into `Transaction` objects; raises `ValueError` on malformed data |
| `merge.py` | Joins several statements and drops duplicates by transaction `id` |
| `rules.py` | Loads and validates the TOML rules and the ignore keywords |
| `categorizer.py` | Assigns a category to each transaction, removes ignored ones, builds the `Overview` |
| `periods.py` | Labels a date as a year, quarter, month, ISO week or day |
| `export.py` | Turns the overviews into CSV or JSON and writes the file |
| `models.py` | `Transaction` (immutable), `Transactions` (an import) and `Overview` |
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

## Limitations (v0.2)

- Only the Moneta XML format.
- Categories come from keyword rules only; there is no learning and no manual editing of
  single transactions.
- The export has no option to overwrite a file.

See [docs/ROADMAP.md](docs/ROADMAP.md) for progress.

## License

[MIT](LICENSE)
