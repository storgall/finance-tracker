import csv
import io
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from finance_tracker.export import export_overviews, to_csv, to_json
from finance_tracker.models import Overview, Transaction, Transactions


def make_overview(
    income: dict[str, str] | None = None, expenses: dict[str, str] | None = None
) -> Overview:
    """Expenses are given as negative numbers, like in a real Overview."""
    return Overview(
        income={name: Decimal(amount) for name, amount in (income or {}).items()},
        expenses={name: Decimal(amount) for name, amount in (expenses or {}).items()},
    )


def make_transactions(count: int = 3, skipped: int = 0, ignored: int = 0) -> Transactions:
    return Transactions(
        transactions=[
            Transaction(
                id=f"TX{n}",
                date=date(2026, 9, 3),
                amount=Decimal("-1.00"),
                counterparty="Test",
                description="Test",
            )
            for n in range(count)
        ],
        skipped=skipped,
        ignored=ignored,
    )


def parse(text: str) -> dict[str, Any]:
    document: dict[str, Any] = json.loads(text)
    return document


SEPTEMBER = make_overview(
    income={"Salary": "25000.00"}, expenses={"Rent": "-12000.00", "Groceries": "-125.50"}
)
OCTOBER = make_overview(expenses={"Uncategorized": "-50.00"})


# --- CSV ---------------------------------------------------------------------------------


def test_csv_has_a_header_and_one_row_per_period_and_category() -> None:
    text = to_csv({"2026-09": SEPTEMBER, "2026-10": OCTOBER})

    assert text.splitlines() == [
        "period,kind,category,amount",
        "2026-09,income,Salary,25000.00",
        "2026-09,expense,Rent,12000.00",
        "2026-09,expense,Groceries,125.50",
        "2026-10,expense,Uncategorized,50.00",
    ]


def test_csv_ends_with_a_newline_and_uses_unix_line_endings() -> None:
    text = to_csv({"all": OCTOBER})

    assert text.endswith("\n")
    assert "\r" not in text


def test_csv_lists_income_before_expenses_inside_a_period() -> None:
    overview = make_overview(income={"Gift": "10.00"}, expenses={"Rent": "-5.00"})

    rows = list(csv.reader(io.StringIO(to_csv({"all": overview}))))[1:]

    assert [row[1] for row in rows] == ["income", "expense"]


def test_csv_keeps_the_order_of_the_periods_and_categories() -> None:
    overviews = {"2026-10": OCTOBER, "2026-09": SEPTEMBER}

    rows = list(csv.reader(io.StringIO(to_csv(overviews))))[1:]

    assert [row[0] for row in rows] == ["2026-10", "2026-09", "2026-09", "2026-09"]


def test_csv_amounts_are_never_negative_and_have_two_decimals() -> None:
    overview = make_overview(income={"A": "1500"}, expenses={"B": "-7"})

    rows = list(csv.reader(io.StringIO(to_csv({"all": overview}))))[1:]

    assert [row[3] for row in rows] == ["1500.00", "7.00"]


def test_csv_quotes_values_with_a_comma_or_a_quote() -> None:
    overview = make_overview(expenses={'Food, "fast"': "-9.90"})

    text = to_csv({"all": overview})

    assert text.splitlines()[1] == 'all,expense,"Food, ""fast""",9.90'
    assert list(csv.reader(io.StringIO(text)))[1][2] == 'Food, "fast"'


def test_csv_keeps_non_ascii_characters() -> None:
    assert "Nájem" in to_csv({"all": make_overview(expenses={"Nájem": "-1.00"})})


def test_csv_without_periods_is_only_the_header() -> None:
    assert to_csv({}).splitlines() == ["period,kind,category,amount"]


def test_csv_period_without_categories_adds_no_rows() -> None:
    assert to_csv({"2026-09": make_overview()}).splitlines() == ["period,kind,category,amount"]


# --- JSON --------------------------------------------------------------------------------


def test_json_has_the_counts_of_the_import() -> None:
    document = parse(to_json(make_transactions(count=5, skipped=1, ignored=2), {}))

    assert document["imported"] == 5
    assert document["skipped"] == 1
    assert document["ignored"] == 2


def test_json_describes_every_period() -> None:
    document = parse(to_json(make_transactions(), {"2026-09": SEPTEMBER, "2026-10": OCTOBER}))

    assert document["periods"] == [
        {
            "period": "2026-09",
            "income": {"Salary": "25000.00"},
            "expenses": {"Rent": "12000.00", "Groceries": "125.50"},
            "total_income": "25000.00",
            "total_expenses": "12125.50",
            "net_total": "12874.50",
        },
        {
            "period": "2026-10",
            "income": {},
            "expenses": {"Uncategorized": "50.00"},
            "total_income": "0.00",
            "total_expenses": "50.00",
            "net_total": "-50.00",
        },
    ]


def test_json_amounts_are_strings_so_no_precision_is_lost() -> None:
    overview = make_overview(income={"A": "0.10"}, expenses={"B": "-0.20"})

    period = parse(to_json(make_transactions(), {"all": overview}))["periods"][0]

    assert period["income"] == {"A": "0.10"}
    assert period["total_expenses"] == "0.20"
    assert period["net_total"] == "-0.10"


def test_json_keeps_the_order_of_periods_and_categories() -> None:
    overviews = {"2026-10": OCTOBER, "2026-09": SEPTEMBER}

    periods = parse(to_json(make_transactions(), overviews))["periods"]

    assert [p["period"] for p in periods] == ["2026-10", "2026-09"]
    assert list(periods[1]["expenses"]) == ["Rent", "Groceries"]


def test_json_without_periods_has_an_empty_list() -> None:
    assert parse(to_json(make_transactions(), {}))["periods"] == []


def test_json_keeps_non_ascii_characters_readable() -> None:
    overview = make_overview(expenses={"Nájem": "-1.00"})

    text = to_json(make_transactions(), {"all": overview})

    assert "Nájem" in text
    assert "\\u" not in text


def test_json_is_indented_and_ends_with_a_newline() -> None:
    text = to_json(make_transactions(), {})

    assert text.endswith("\n")
    assert text.splitlines()[1].startswith('  "')


# --- writing a file ----------------------------------------------------------------------


def test_csv_extension_writes_the_csv_text(tmp_path: Path) -> None:
    target = tmp_path / "overview.csv"

    export_overviews(target, make_transactions(), {"all": SEPTEMBER})

    assert target.read_text(encoding="utf-8") == to_csv({"all": SEPTEMBER})


def test_json_extension_writes_the_json_text(tmp_path: Path) -> None:
    target = tmp_path / "overview.json"
    transactions = make_transactions(count=4, skipped=1)

    export_overviews(target, transactions, {"all": SEPTEMBER})

    assert target.read_text(encoding="utf-8") == to_json(transactions, {"all": SEPTEMBER})


def test_extension_is_matched_regardless_of_letter_case(tmp_path: Path) -> None:
    export_overviews(tmp_path / "a.CSV", make_transactions(), {"all": SEPTEMBER})
    export_overviews(tmp_path / "b.Json", make_transactions(), {"all": SEPTEMBER})

    assert (tmp_path / "a.CSV").read_text(encoding="utf-8").startswith("period,")
    assert (tmp_path / "b.Json").read_text(encoding="utf-8").startswith("{")


def test_unsupported_extension_raises_value_error_and_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "overview.txt"

    with pytest.raises(ValueError, match=r"\.txt.*\.csv.*\.json"):
        export_overviews(target, make_transactions(), {"all": SEPTEMBER})

    assert not target.exists()


def test_file_without_extension_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"\.csv.*\.json"):
        export_overviews(tmp_path / "overview", make_transactions(), {})


def test_existing_file_is_not_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "overview.csv"
    target.write_text("precious data", encoding="utf-8")

    with pytest.raises(FileExistsError, match="overview.csv"):
        export_overviews(target, make_transactions(), {"all": SEPTEMBER})

    assert target.read_text(encoding="utf-8") == "precious data"


def test_missing_folder_raises_file_not_found_error_and_is_not_created(tmp_path: Path) -> None:
    target = tmp_path / "missing" / "overview.csv"

    with pytest.raises(FileNotFoundError):
        export_overviews(target, make_transactions(), {"all": SEPTEMBER})

    assert not (tmp_path / "missing").exists()


def test_file_is_utf8_with_unix_line_endings(tmp_path: Path) -> None:
    target = tmp_path / "overview.csv"
    overview = make_overview(expenses={"Nájem": "-1.00"})

    export_overviews(target, make_transactions(), {"all": overview})

    raw = target.read_bytes()
    assert "Nájem".encode() in raw
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
