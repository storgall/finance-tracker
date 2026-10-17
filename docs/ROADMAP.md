# Roadmap — finance-tracker

Updated by `/py:next-step` after each finished step. One step = a small change that leaves a runnable version.

## M1 — First runnable version

- [x] 1. `Transaction` data model (date, amount as `Decimal`, counterparty, description) with a test.
- [x] 2. XML parser: Moneta statement export → `list[Transaction]`, tested on a made-up `tests/fixtures/sample_statement.xml`.
- [x] 3. CLI: `finance-tracker import <file>` prints the number of imported transactions.
- [x] 4. Rule-based categorization (keyword in description → category).
  - [x] 4a. `categorize(transaction, rules)`: case-insensitive keyword match, first rule wins, `Uncategorized` fallback.
  - [x] 4b. `load_rules(path)`: read rules from a TOML file (`data/rules.toml`, example in `rules.example.toml`).
  - [x] 4c. CLI option `--rules` (default `data/rules.toml`) for the `import` command.
- [x] 5. Monthly overview: sum of expenses per category, printed in the CLI.
  - [x] 5a. `Overview` with income and expenses per category, biggest first; printed by `import`.
  - [x] 5b. Period header (first and last transaction date) and totals: total income, total expenses, balance.
  - [x] 5c. README: install, usage example with `rules.example.toml`, how to export the Moneta XML.

## M2 — v0.2.0

Order matters: export comes after periods, because periods change the shape of the overview. The version number in `pyproject.toml` stays `0.1.0` until the last step.

- [x] 1. `--version` (reads the installed package version via `importlib.metadata`).
- [x] 2. Several statement files in one run (`import a.xml b.xml`); duplicates are dropped by the transaction `id` (new `Transaction.id` field).
- [x] 2b. Folders: a path given to `import` may be a folder; its `*.xml` files are read (not recursive, sorted by name, an empty folder is an error). Function `expand_paths`.
- [x] 3. Ignore rules: `[ignore] keywords = [...]` in `rules.toml`, same matching as categories; ignored count is printed.
- [x] 4. Periods: `--by {year,quarter,month,week,day}` (ISO weeks); without it the overview stays one total.
- [x] 5. Export: `--export file.csv|file.json` (format by extension; amounts as strings in JSON).
- [ ] 6. Release 0.2.0: bump the version, update README, tag.

## Out of scope (v0.1)

Web UI, database, charts, multiple banks.
