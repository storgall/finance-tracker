from datetime import date
from decimal import Decimal

from finance_tracker.merge import merge_transactions
from finance_tracker.models import Transaction


def make_transaction(transaction_id: str) -> Transaction:
    return Transaction(
        id=transaction_id,
        date=date(2026, 9, 3),
        amount=Decimal("-10.00"),
        counterparty="Test Market",
        description=f"Payment {transaction_id}",
    )


def ids(transactions: list[Transaction]) -> list[str]:
    return [t.id for t in transactions]


def test_no_batches_gives_empty_list_and_nothing_skipped() -> None:
    assert merge_transactions([]) == ([], 0)


def test_only_empty_batches_give_empty_list_and_nothing_skipped() -> None:
    assert merge_transactions([[], []]) == ([], 0)


def test_single_batch_is_returned_unchanged() -> None:
    batch = [make_transaction("A"), make_transaction("B")]

    assert merge_transactions([batch]) == (batch, 0)


def test_batches_without_overlap_are_joined_in_order() -> None:
    first = [make_transaction("A"), make_transaction("B")]
    second = [make_transaction("C")]

    merged, skipped = merge_transactions([first, second])

    assert ids(merged) == ["A", "B", "C"]
    assert skipped == 0


def test_transaction_present_in_two_batches_is_kept_once_and_counted_as_skipped() -> None:
    first = [make_transaction("A"), make_transaction("B")]
    second = [make_transaction("B"), make_transaction("C")]

    merged, skipped = merge_transactions([first, second])

    assert ids(merged) == ["A", "B", "C"]
    assert skipped == 1


def test_identical_batches_give_just_one_copy() -> None:
    batch = [make_transaction("A"), make_transaction("B")]

    merged, skipped = merge_transactions([batch, list(batch), list(batch)])

    assert merged == batch
    assert skipped == 4


def test_duplicate_inside_a_single_batch_is_dropped_and_counted() -> None:
    batch = [make_transaction("A"), make_transaction("B"), make_transaction("A")]

    merged, skipped = merge_transactions([batch])

    assert ids(merged) == ["A", "B"]
    assert skipped == 1


def test_original_order_is_kept_not_sorted_by_id() -> None:
    batch = [make_transaction("C"), make_transaction("A"), make_transaction("B")]

    merged, _ = merge_transactions([batch])

    assert ids(merged) == ["C", "A", "B"]


def test_skipped_plus_merged_equals_all_input_transactions() -> None:
    batches = [
        [make_transaction("A"), make_transaction("B")],
        [make_transaction("B"), make_transaction("C"), make_transaction("A")],
    ]

    merged, skipped = merge_transactions(batches)

    assert len(merged) + skipped == sum(len(batch) for batch in batches)


def test_input_lists_are_not_modified_and_a_new_list_is_returned() -> None:
    first = [make_transaction("A"), make_transaction("B")]
    second = [make_transaction("B"), make_transaction("C")]

    merged, _ = merge_transactions([first, second])

    assert ids(first) == ["A", "B"]
    assert ids(second) == ["B", "C"]
    assert merged is not first
    assert merged is not second
