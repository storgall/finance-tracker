import sys
from argparse import ArgumentParser
from importlib import metadata
from pathlib import Path

from finance_tracker.categorizer import (
    categorize_by_period,
    categorize_transactions,
    remove_ignored,
)
from finance_tracker.files import expand_paths
from finance_tracker.models import Overview, Transaction, Transactions
from finance_tracker.parser import parse_statements
from finance_tracker.periods import GRANULARITIES
from finance_tracker.rules import load_rules


def main(argv: list[str] | None = None) -> None:
    """Run the command line interface.

    The ``import`` command reads the statements, removes duplicates and ignored transactions,
    and prints an overview of income and expenses per category: one for the whole import, or
    one for every period when ``--by`` is given. A problem with the input is reported on
    ``stderr`` and ends the program with exit code 1; invalid arguments end it with code 2
    (``argparse``).

    Args:
        argv: the arguments without the program name. ``None`` means ``sys.argv``; tests pass
            a list.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        try:
            transactions = parse_statements(
                expand_paths(args.paths, expand_subfolders=args.recursive)
            )
            rule_set = load_rules(args.rules)
        except (ValueError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        transactions = remove_ignored(transactions, rule_set.ignore)
        _print_header(transactions)

        if args.by:
            categorized_by_periods = categorize_by_period(
                transactions.transactions, rule_set.categories, args.by
            )
            for period, overview in categorized_by_periods.items():
                _print_period(period, overview)
        else:
            categorized = categorize_transactions(transactions.transactions, rule_set.categories)
            print()
            _print_overview(categorized)


def _build_parser() -> ArgumentParser:
    """Define the commands and options of the program (only the definition, no parsing)."""
    parser = ArgumentParser(prog="finance-tracker")

    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a statement")
    import_parser.add_argument("paths", help="Paths to the statement files", type=Path, nargs="+")
    import_parser.add_argument(
        "--rules", help="Path to the rules file", type=Path, default=Path("data/rules.toml")
    )
    import_parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively search for XML files in subfolders",
    )
    import_parser.add_argument("--by", help="Split the overview by period", choices=GRANULARITIES)

    parser.add_argument(
        "--version",
        help="Show the version of the application",
        action="version",
        version=f"%(prog)s {metadata.version('finance-tracker')}",
    )

    return parser


def _print_header(transactions: Transactions) -> None:
    """Print how many transactions were imported, skipped and ignored, and their date range.

    The ``Skipped`` and ``Ignored`` lines appear only when something was skipped or ignored.
    """
    print(f"Imported {len(transactions.transactions)} transactions")
    if transactions.skipped:
        print(f"Skipped {transactions.skipped} duplicate transactions")
    if transactions.ignored:
        print(f"Ignored {transactions.ignored} transactions")

    _print_dates(transactions.transactions)


def _print_period(period: str, overview: Overview) -> None:
    """Print the heading of a period (``== 2026-09 ==``) followed by its overview."""
    print(f"\n== {period} ==")
    _print_overview(overview)


def _print_overview(overview: Overview) -> None:
    """Print the totals, then the income and the expenses per category.

    Expenses are shown as positive numbers; the categories are listed biggest first.
    """
    _print_totals(overview)

    print("\nIncome:")
    for category, total in overview.income.items():
        print(f"  {category}: {total:.2f}")

    print("\nExpenses:")
    for category, total in overview.expenses.items():
        print(f"  {category}: {-total:.2f}")


def _print_dates(transactions: list[Transaction]) -> None:
    """Print the first and the last date of ``transactions``; print nothing if there are none."""
    if not transactions:
        return

    dates = [transaction.date for transaction in transactions]
    print(f"Date range: {min(dates)} to {max(dates)}")


def _print_totals(overview: Overview) -> None:
    """Print the total income, the total expenses (as a positive number) and the balance."""
    print(f"Total Income: {overview.total_income:.2f}")
    print(f"Total Expenses: {-overview.total_expenses:.2f}")
    print(f"Net Total: {overview.net_total:.2f}")
