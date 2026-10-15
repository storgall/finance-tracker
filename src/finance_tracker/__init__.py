import sys
from argparse import ArgumentParser
from pathlib import Path

from finance_tracker.categorizer import categorize_transactions
from finance_tracker.models import Overview, Transaction
from finance_tracker.parser import parse_statement
from finance_tracker.rules import load_rules


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        try:
            transactions = parse_statement(args.path)
            rules = load_rules(args.rules)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        categorized = categorize_transactions(transactions, rules)
        _print_overview(transactions, categorized)


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="finance-tracker")

    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a statement")
    import_parser.add_argument("path", help="Path to the statement file", type=Path)
    import_parser.add_argument(
        "--rules", help="Path to the rules file", type=Path, default=Path("data/rules.toml")
    )

    return parser


def _print_overview(transactions: list[Transaction], overview: Overview) -> None:
    print(f"Imported {len(transactions)} transactions")

    _print_dates(transactions)

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
