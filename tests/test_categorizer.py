from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.categorizer import UNCATEGORIZED, categorize, categorize_transactions
from finance_tracker.models import Transaction
from finance_tracker.rules import Rules


def make_transaction(
    counterparty: str = "", description: str = "", amount: str = "-100.00"
) -> Transaction:
    return Transaction(
        id="TX1",
        date=date(2026, 9, 3),
        amount=Decimal(amount),
        counterparty=counterparty,
        description=description,
    )


def test_matches_keyword_in_counterparty() -> None:
    rules: Rules = {"Groceries": ["market"]}

    assert categorize(make_transaction(counterparty="Test Market s.r.o."), rules) == "Groceries"


def test_matches_keyword_in_description() -> None:
    rules: Rules = {"Streaming": ["streaming"]}

    assert categorize(make_transaction(description="Fake streaming monthly"), rules) == "Streaming"


def test_matching_ignores_letter_case() -> None:
    rules: Rules = {"Groceries": ["MARKET"], "Rent": ["nájem"]}

    assert categorize(make_transaction(counterparty="test market"), rules) == "Groceries"
    assert categorize(make_transaction(description="NÁJEM září"), rules) == "Rent"


def test_any_keyword_of_a_rule_can_match() -> None:
    rules: Rules = {"Groceries": ["market", "albert", "shop"]}

    assert categorize(make_transaction(counterparty="Albert Hypermarket"), rules) == "Groceries"


def test_first_matching_rule_wins() -> None:
    transaction = make_transaction(counterparty="Test Market")

    assert categorize(transaction, {"Food": ["market"], "Shopping": ["market"]}) == "Food"
    assert categorize(transaction, {"Shopping": ["market"], "Food": ["market"]}) == "Shopping"


def test_no_matching_rule_returns_uncategorized() -> None:
    rules: Rules = {"Groceries": ["market"]}

    assert categorize(make_transaction(counterparty="Unknown Shop"), rules) == UNCATEGORIZED


def test_empty_rules_return_uncategorized() -> None:
    assert categorize(make_transaction(counterparty="Test Market"), {}) == UNCATEGORIZED


@pytest.mark.parametrize("keyword", ["", " ", "   ", "\t"])
def test_empty_or_whitespace_keyword_never_matches(keyword: str) -> None:
    rules: Rules = {"Everything": [keyword]}

    assert categorize(make_transaction(counterparty="Test Market"), rules) == UNCATEGORIZED


def test_blank_keyword_does_not_hide_later_valid_keywords() -> None:
    rules: Rules = {"Groceries": [" ", "market"]}

    assert categorize(make_transaction(counterparty="Test Market"), rules) == "Groceries"


def test_income_is_categorized_like_expenses() -> None:
    rules: Rules = {"Salary": ["výplata"]}
    income = make_transaction(description="Výplata září", amount="25000.00")

    assert categorize(income, rules) == "Salary"


def test_categorize_transactions_sums_expenses_per_category() -> None:
    rules: Rules = {"Groceries": ["market"], "Rent": ["nájem"]}
    transactions = [
        make_transaction(counterparty="Test Market", amount="-100.50"),
        make_transaction(counterparty="Another Market", amount="-20.25"),
        make_transaction(description="nájem září", amount="-12000.00"),
    ]

    overview = categorize_transactions(transactions, rules)

    assert overview.expenses == {"Rent": Decimal("-12000.00"), "Groceries": Decimal("-120.75")}
    assert overview.income == {}


def test_categorize_transactions_separates_income_from_expenses() -> None:
    rules: Rules = {"Salary": ["výplata"], "Groceries": ["market"]}
    transactions = [
        make_transaction(description="Výplata září", amount="25000.00"),
        make_transaction(counterparty="Test Market", amount="-100.00"),
    ]

    overview = categorize_transactions(transactions, rules)

    assert overview.income == {"Salary": Decimal("25000.00")}
    assert overview.expenses == {"Groceries": Decimal("-100.00")}


def test_categorize_transactions_uses_uncategorized_for_unmatched() -> None:
    transactions = [make_transaction(counterparty="Unknown", amount="-5.00")]

    overview = categorize_transactions(transactions, {})

    assert overview.expenses == {UNCATEGORIZED: Decimal("-5.00")}


def test_categorize_transactions_without_transactions_gives_empty_overview() -> None:
    overview = categorize_transactions([], {"Groceries": ["market"]})

    assert overview.expenses == {}
    assert overview.income == {}


def test_categorize_transactions_sorts_biggest_expense_first() -> None:
    rules: Rules = {"Small": ["small"], "Big": ["big"]}
    transactions = [
        make_transaction(counterparty="small shop", amount="-10.00"),
        make_transaction(counterparty="big shop", amount="-900.00"),
    ]

    overview = categorize_transactions(transactions, rules)

    assert list(overview.expenses) == ["Big", "Small"]


def test_zero_amount_counts_as_income_not_expense() -> None:
    transactions = [make_transaction(counterparty="Test", amount="0.00")]

    overview = categorize_transactions(transactions, {})

    assert overview.expenses == {}
    assert overview.income == {UNCATEGORIZED: Decimal("0.00")}
