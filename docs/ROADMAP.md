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

## Out of scope (v0.1)

Web UI, database, charts, multiple banks.
