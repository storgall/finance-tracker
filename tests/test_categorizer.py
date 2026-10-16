from datetime import date
from decimal import Decimal

import pytest

from finance_tracker.categorizer import (
    UNCATEGORIZED,
    categorize,
    categorize_transactions,
    is_ignored,
    remove_ignored,
)
from finance_tracker.models import Transaction, Transactions
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


def test_transaction_is_ignored_when_keyword_is_in_counterparty() -> None:
    transaction = make_transaction(counterparty="999999999/0600")

    assert is_ignored(transaction, ["999999999/0600"]) is True


def test_transaction_is_ignored_when_keyword_is_in_description() -> None:
    transaction = make_transaction(description="Transfer to savings")

    assert is_ignored(transaction, ["savings"]) is True


def test_ignoring_ignores_letter_case() -> None:
    transaction = make_transaction(counterparty="Fake Savings")

    assert is_ignored(transaction, ["FAKE SAVINGS"]) is True
    assert is_ignored(make_transaction(description="NÁJEM"), ["nájem"]) is True


def test_any_of_several_keywords_can_ignore_a_transaction() -> None:
    transaction = make_transaction(counterparty="Fake Savings")

    assert is_ignored(transaction, ["other", "savings", "another"]) is True


def test_transaction_without_matching_keyword_is_not_ignored() -> None:
    transaction = make_transaction(counterparty="Test Market")

    assert is_ignored(transaction, ["savings"]) is False


def test_no_keywords_ignore_nothing() -> None:
    assert is_ignored(make_transaction(counterparty="Test Market"), []) is False


@pytest.mark.parametrize("keyword", ["", " ", "   ", "\t"])
def test_empty_or_whitespace_keyword_never_ignores(keyword: str) -> None:
    assert is_ignored(make_transaction(counterparty="Test Market"), [keyword]) is False


def test_blank_keyword_does_not_hide_later_valid_keywords_when_ignoring() -> None:
    transaction = make_transaction(counterparty="Fake Savings")

    assert is_ignored(transaction, [" ", "savings"]) is True


def test_ignoring_does_not_depend_on_amount() -> None:
    expense = make_transaction(counterparty="Fake Savings", amount="-500.00")
    income = make_transaction(counterparty="Fake Savings", amount="500.00")

    assert is_ignored(expense, ["savings"]) is True
    assert is_ignored(income, ["savings"]) is True


def make_transactions(*transactions: Transaction, skipped: int = 0) -> Transactions:
    return Transactions(transactions=list(transactions), skipped=skipped, ignored=0)


def test_remove_ignored_drops_matching_transactions_and_counts_them() -> None:
    savings = make_transaction(counterparty="Fake Savings", amount="-500.00")
    market = make_transaction(counterparty="Test Market", amount="-100.00")
    rent = make_transaction(description="nájem září", amount="-12000.00")

    result = remove_ignored(make_transactions(savings, market, rent), ["savings"])

    assert result.transactions == [market, rent]
    assert result.ignored == 1


def test_remove_ignored_counts_every_removed_transaction() -> None:
    transactions = make_transactions(
        make_transaction(counterparty="Fake Savings", amount="-500.00"),
        make_transaction(description="Transfer to savings", amount="500.00"),
        make_transaction(counterparty="Test Market"),
    )

    result = remove_ignored(transactions, ["savings"])

    assert len(result.transactions) == 1
    assert result.ignored == 2


def test_remove_ignored_with_several_keywords() -> None:
    transactions = make_transactions(
        make_transaction(counterparty="Fake Savings"),
        make_transaction(counterparty="999999999/0600"),
        make_transaction(counterparty="Test Market"),
    )

    result = remove_ignored(transactions, ["savings", "999999999/0600"])

    assert [t.counterparty for t in result.transactions] == ["Test Market"]
    assert result.ignored == 2


def test_remove_ignored_without_keywords_keeps_everything() -> None:
    transactions = make_transactions(make_transaction(counterparty="Fake Savings"))

    result = remove_ignored(transactions, [])

    assert len(result.transactions) == 1
    assert result.ignored == 0


def test_remove_ignored_when_nothing_matches_keeps_everything() -> None:
    transactions = make_transactions(make_transaction(counterparty="Test Market"))

    result = remove_ignored(transactions, ["savings"])

    assert len(result.transactions) == 1
    assert result.ignored == 0


def test_remove_ignored_ignores_blank_keywords() -> None:
    transactions = make_transactions(make_transaction(counterparty="Test Market"))

    result = remove_ignored(transactions, ["", "  "])

    assert len(result.transactions) == 1
    assert result.ignored == 0


def test_remove_ignored_keeps_the_skipped_duplicates_count() -> None:
    transactions = make_transactions(
        make_transaction(counterparty="Fake Savings"),
        make_transaction(counterparty="Test Market"),
        skipped=3,
    )

    result = remove_ignored(transactions, ["savings"])

    assert result.skipped == 3
    assert result.ignored == 1


def test_remove_ignored_on_no_transactions_does_nothing() -> None:
    result = remove_ignored(make_transactions(), ["savings"])

    assert result.transactions == []
    assert result.ignored == 0
