from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.models import Overview, Transaction


def make_transaction(amount: str = "-125.50") -> Transaction:
    return Transaction(
        date=date(2026, 9, 3),
        amount=Decimal(amount),
        counterparty="Test Market s.r.o.",
        description="Card payment",
    )


def test_fields_are_stored() -> None:
    tx = make_transaction()

    assert tx.date == date(2026, 9, 3)
    assert tx.amount == Decimal("-125.50")
    assert tx.counterparty == "Test Market s.r.o."
    assert tx.description == "Card payment"


def test_transactions_with_same_values_are_equal() -> None:
    assert make_transaction() == make_transaction()
    assert make_transaction("-1.00") != make_transaction("-2.00")


def test_transaction_is_immutable() -> None:
    tx = make_transaction()

    with pytest.raises(FrozenInstanceError):
        tx.amount = Decimal("0")  # type: ignore[misc]


def test_negative_amount_is_expense() -> None:
    assert make_transaction("-0.01").is_expense is True


@pytest.mark.parametrize("amount", ["0", "0.00", "1500.00"])
def test_zero_or_positive_amount_is_not_expense(amount: str) -> None:
    assert make_transaction(amount).is_expense is False


def test_overview_add_puts_expenses_and_income_into_separate_dicts() -> None:
    overview = Overview(expenses={}, income={})

    overview.add(True, "Groceries", Decimal("-100.00"))
    overview.add(False, "Salary", Decimal("25000.00"))

    assert overview.expenses == {"Groceries": Decimal("-100.00")}
    assert overview.income == {"Salary": Decimal("25000.00")}


def test_overview_add_sums_amounts_of_the_same_category() -> None:
    overview = Overview(expenses={}, income={})

    overview.add(True, "Groceries", Decimal("-100.50"))
    overview.add(True, "Groceries", Decimal("-20.25"))

    assert overview.expenses == {"Groceries": Decimal("-120.75")}


def test_overview_sort_puts_biggest_expense_first() -> None:
    overview = Overview(
        expenses={"Small": Decimal("-10.00"), "Big": Decimal("-500.00"), "Mid": Decimal("-50.00")},
        income={},
    )

    overview.sort()

    assert list(overview.expenses) == ["Big", "Mid", "Small"]


def test_overview_sort_puts_biggest_income_first() -> None:
    overview = Overview(
        expenses={},
        income={"Small": Decimal("10.00"), "Big": Decimal("500.00"), "Mid": Decimal("50.00")},
    )

    overview.sort()

    assert list(overview.income) == ["Big", "Mid", "Small"]


def test_overview_totals_sum_all_categories() -> None:
    overview = Overview(
        expenses={"Rent": Decimal("-12000.00"), "Groceries": Decimal("-125.50")},
        income={"Salary": Decimal("25000.00"), "Gift": Decimal("500.00")},
    )

    assert overview.total_expenses == Decimal("-12125.50")
    assert overview.total_income == Decimal("25500.00")


def test_overview_net_total_is_income_plus_expenses() -> None:
    overview = Overview(
        expenses={"Rent": Decimal("-12000.00")},
        income={"Salary": Decimal("25000.00")},
    )

    assert overview.net_total == Decimal("13000.00")


def test_overview_net_total_is_negative_when_spending_exceeds_income() -> None:
    overview = Overview(
        expenses={"Rent": Decimal("-12000.00")},
        income={"Salary": Decimal("1000.00")},
    )

    assert overview.net_total == Decimal("-11000.00")


def test_empty_overview_has_zero_decimal_totals() -> None:
    overview = Overview(expenses={}, income={})

    assert overview.total_expenses == Decimal("0.00")
    assert overview.total_income == Decimal("0.00")
    assert overview.net_total == Decimal("0.00")
    assert isinstance(overview.net_total, Decimal)


def test_overview_totals_follow_later_additions() -> None:
    overview = Overview(expenses={}, income={})

    overview.add(True, "Groceries", Decimal("-10.00"))
    overview.add(False, "Salary", Decimal("100.00"))

    assert overview.net_total == Decimal("90.00")
