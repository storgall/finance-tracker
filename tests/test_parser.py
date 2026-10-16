from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_tracker.models import Transaction
from finance_tracker.parser import parse_statement

FIXTURE = Path(__file__).parent / "fixtures" / "sample_statement.xml"


def write_xml(tmp_path: Path, transactions_xml: str) -> Path:
    path = tmp_path / "statement.xml"
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f"<statement><transactions>{transactions_xml}</transactions></statement>",
        encoding="utf-8",
    )
    return path


def test_parses_all_transactions_in_file_order() -> None:
    transactions = parse_statement(FIXTURE)

    assert [t.amount for t in transactions] == [
        Decimal("-125.50"),
        Decimal("25000.00"),
        Decimal("-12000.00"),
        Decimal("-99.99"),
    ]


def test_maps_all_fields_of_first_transaction() -> None:
    first = parse_statement(FIXTURE)[0]

    assert first == Transaction(
        id="000001A000000000001",
        date=date(2026, 9, 3),
        amount=Decimal("-125.50"),
        counterparty="TEST MARKET S.R.O.",
        description="Platba kartou - Příbram",
    )


def test_income_is_positive() -> None:
    income = parse_statement(FIXTURE)[1]

    assert income.amount == Decimal("25000.00")
    assert income.is_expense is False


def test_multiple_description_messages_are_joined_with_space() -> None:
    rent = parse_statement(FIXTURE)[2]

    assert rent.description == "Trvalý příkaz nájem září"


def test_non_description_messages_are_ignored() -> None:
    streaming = parse_statement(FIXTURE)[3]

    assert streaming.description == "Platba kartou - online"


def test_file_without_transactions_returns_empty_list(tmp_path: Path) -> None:
    assert parse_statement(write_xml(tmp_path, "")) == []


def test_missing_optional_fields_become_empty_strings(tmp_path: Path) -> None:
    path = write_xml(tmp_path, '<transaction id="1" amount="-1.00" date-eff="2026-09-01"/>')

    tx = parse_statement(path)[0]

    assert tx.counterparty == ""
    assert tx.description == ""


@pytest.mark.parametrize(
    ("attributes", "missing"),
    [
        ('id="1" date-eff="2026-09-01"', "amount"),
        ('id="1" amount="-1.00"', "date-eff"),
        ('amount="-1.00" date-eff="2026-09-01"', "id"),
    ],
)
def test_missing_required_attribute_raises_value_error(
    tmp_path: Path, attributes: str, missing: str
) -> None:
    path = write_xml(tmp_path, f"<transaction {attributes}/>")

    with pytest.raises(ValueError, match=missing):
        parse_statement(path)


def test_invalid_amount_raises_value_error_with_the_bad_value(tmp_path: Path) -> None:
    path = write_xml(tmp_path, '<transaction id="1" amount="12,50 Kc" date-eff="2026-09-01"/>')

    with pytest.raises(ValueError, match="Invalid amount.*12,50 Kc"):
        parse_statement(path)


def test_missing_amount_is_reported_as_missing_not_invalid(tmp_path: Path) -> None:
    path = write_xml(tmp_path, '<transaction id="1" date-eff="2026-09-01"/>')

    with pytest.raises(ValueError, match="Missing required attribute 'amount'"):
        parse_statement(path)


def test_invalid_date_raises_value_error(tmp_path: Path) -> None:
    path = write_xml(tmp_path, '<transaction id="1" amount="-1.00" date-eff="03.09.2026"/>')

    with pytest.raises(ValueError, match="03.09.2026"):
        parse_statement(path)


def test_malformed_xml_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.xml"
    path.write_text("<statement><transactions>", encoding="utf-8")

    with pytest.raises(ValueError, match="Failed to parse XML"):
        parse_statement(path)


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_statement(tmp_path / "does_not_exist.xml")


def test_reads_the_id_of_every_transaction() -> None:
    transactions = parse_statement(FIXTURE)

    assert [t.id for t in transactions] == [
        "000001A000000000001",
        "000002A000000000002",
        "000003A000000000003",
        "000004A000000000004",
    ]
