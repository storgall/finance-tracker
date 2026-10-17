import csv
import io
import json
from pathlib import Path

from finance_tracker.models import Overview, Transactions

ALLOWED_FILES = (".csv", ".json")
"""The file extensions ``export_overviews`` can write, in lower case."""


def to_csv(overviews: dict[str, Overview]) -> str:
    """Turn the overviews of the periods into CSV text, one row per period and category.

    Args:
        overviews: period label -> overview, in the order they should appear. For an import
            that is not split by period the caller uses one period, for example ``"all"``.

    Returns:
        CSV text (comma separated, every line ends with a Unix newline) with the header
        ``period,kind,category,amount`` and then, for every period in the given order, first
        its income rows and then its expense rows, each in the order of the overview.

        * ``kind`` is ``income`` or ``expense``
        * ``amount`` is never negative: an expense is written as a positive number, like in
          the printed report, and always has two decimals (``12000.00``)
        * values that contain a comma or a quote are quoted correctly (use the ``csv`` module)

    Requirements:
        * no periods, or periods without any category, give just the header line
    """

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["period", "kind", "category", "amount"])

    for label, overview in overviews.items():
        writer.writerows(_overview_to_csv(label, overview))

    return out.getvalue()


def _overview_to_csv(label: str, overview: Overview) -> list[list[str]]:
    """Return the CSV rows of one period: the income rows first, then the expense rows.

    A row is ``[label, kind, category, amount]``; the amounts are never negative and have two
    decimals. A period without categories gives no rows.
    """
    result = []
    for category, amount in overview.income.items():
        result.append([label, "income", category, f"{amount:.2f}"])
    for category, amount in overview.expenses.items():
        result.append([label, "expense", category, f"{-amount:.2f}"])

    return result


def to_json(transactions: Transactions, overviews: dict[str, Overview]) -> str:
    """Turn an import and the overviews of its periods into JSON text.

    Args:
        transactions: the import; its counts go to the top level of the result.
        overviews: period label -> overview, in the order they should appear.

    Returns:
        JSON text, indented by two spaces, ending with a newline and keeping non-ASCII
        characters as they are (a name like ``nájem`` is not turned into ``\\u`` escapes).
        The document is::

            {
              "imported": 5,
              "skipped": 1,
              "ignored": 0,
              "periods": [
                {
                  "period": "2026-09",
                  "income": {"Salary": "25000.00"},
                  "expenses": {"Rent": "12000.00"},
                  "total_income": "25000.00",
                  "total_expenses": "12000.00",
                  "net_total": "13000.00"
                }
              ]
            }

        (the example is shown with the real indentation of the output: two spaces per level)

        * ``imported`` is the number of transactions in ``transactions`` (``skipped`` and
          ``ignored`` are copied)
        * every amount is a **string** with two decimals, so no precision is lost in JSON
          numbers; expenses and ``total_expenses`` are positive, ``net_total`` keeps its sign
        * ``periods`` keeps the order of ``overviews`` and the categories keep the order of
          the overview; a period without categories has empty ``income`` and ``expenses``
          and totals ``"0.00"``
    """

    data: dict[str, object] = {
        "imported": len(transactions.transactions),
        "skipped": transactions.skipped,
        "ignored": transactions.ignored,
    }

    periods: list[dict[str, object]] = []

    for label, overview in overviews.items():
        periods.append(_overview_to_json(label, overview))

    data["periods"] = periods

    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _overview_to_json(label: str, overview: Overview) -> dict[str, object]:
    """Return one period as a dict that is ready for ``json.dumps``.

    The amounts are strings with two decimals (``Decimal`` is not a JSON type); expenses and
    ``total_expenses`` are positive, ``net_total`` keeps its sign.
    """
    result: dict[str, object] = {}

    result["period"] = label
    result["income"] = {category: f"{amount:.2f}" for category, amount in overview.income.items()}
    result["expenses"] = {
        category: f"{-amount:.2f}" for category, amount in overview.expenses.items()
    }
    result["total_income"] = f"{overview.total_income:.2f}"
    result["total_expenses"] = f"{-overview.total_expenses:.2f}"
    result["net_total"] = f"{overview.net_total:.2f}"

    return result


def export_overviews(
    path: Path, transactions: Transactions, overviews: dict[str, Overview]
) -> None:
    """Write the overviews of an import to a new file; the format follows the extension.

    Args:
        path: the file to create. ``.csv`` gives ``to_csv`` text, ``.json`` gives ``to_json``
            text; the extension is matched regardless of letter case (``.CSV`` works too).
        transactions: the import (used by the JSON format).
        overviews: period label -> overview, as for ``to_csv`` and ``to_json``.

    Raises:
        ValueError: if the extension is not supported; the message names the extension and the
            supported ones. Nothing is written.
        FileExistsError: if ``path`` already exists. The existing file is left untouched; an
            export never overwrites anything.
        FileNotFoundError: if the folder of ``path`` does not exist. No folder is created.

    Requirements:
        * the file is UTF-8 and keeps the ``"\\n"`` line endings of the text exactly, also on
          Windows (no ``"\\r\\n"`` conversion)
        * the extension is checked first, so an unsupported file never gets created
        * no file is created when anything fails

    The file is opened with mode ``"x"``, which fails with ``FileExistsError`` when the file
    exists (so nothing is overwritten), and with ``newline=""`` so that the line endings are
    written as they are.
    """

    match path.suffix.lower():
        case ".csv":
            file_text = to_csv(overviews)
        case ".json":
            file_text = to_json(transactions, overviews)
        case _:
            raise ValueError(
                f"Exporting to {path.suffix.lower()} files not implemented. "
                f"Allowed Files: {ALLOWED_FILES}"
            )

    with open(path, "x", encoding="utf-8", newline="") as file:
        file.write(file_text)
