import sys
from argparse import ArgumentParser
from importlib import metadata
from pathlib import Path

from finance_tracker.categorizer import categorize_transactions, remove_ignored
from finance_tracker.models import Overview, Transaction, Transactions
from finance_tracker.parser import parse_statements
from finance_tracker.rules import load_rules


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        try:
            transactions = parse_statements(args.paths)
            rule_set = load_rules(args.rules)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        transactions = remove_ignored(transactions, rule_set.ignore)
        categorized = categorize_transactions(transactions.transactions, rule_set.categories)
        _print_overview(transactions, categorized)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="finance-tracker")

    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a statement")
    import_parser.add_argument("paths", help="Paths to the statement files", type=Path, nargs="+")
    import_parser.add_argument(
        "--rules", help="Path to the rules file", type=Path, default=Path("data/rules.toml")
    )

    parser.add_argument(
        "--version",
        help="Show the version of the application",
        action="version",
        version=f"%(prog)s {metadata.version('finance-tracker')}",
    )

    return parser


def _print_overview(transactions: Transactions, overview: Overview) -> None:
    print(f"Imported {len(transactions.transactions)} transactions")
    if transactions.skipped:
        print(f"Skipped {transactions.skipped} duplicate transactions")
    if transactions.ignored:
        print(f"Ignored {transactions.ignored} transactions")

    _print_dates(transactions.transactions)

    _print_totals(overview)

    print("\nIncome:")
    for category, total in overview.income.items():
        print(f"  {category}: {total:.2f}")

    print("\nExpenses:")
    for category, total in overview.expenses.items():
        print(f"  {category}: {-total:.2f}")


def _print_dates(transactions: list[Transaction]) -> None:
    if not transactions:
        return

    dates = [transaction.date for transaction in transactions]
    print(f"Date range: {min(dates)} to {max(dates)}")


def _print_totals(overview: Overview) -> None:
    print(f"\nTotal Income: {overview.total_income:.2f}")
    print(f"Total Expenses: {-overview.total_expenses:.2f}")
    print(f"Net Total: {overview.net_total:.2f}")
