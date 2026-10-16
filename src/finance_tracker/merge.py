from finance_tracker.models import Transaction


def merge_transactions(batches: list[list[Transaction]]) -> tuple[list[Transaction], int]:
    """Join transactions from several statements into one list without duplicates.

    Statements exported from the bank can overlap, so the same transaction (same ``id``)
    may appear in more than one batch.

    Args:
        batches: one list of transactions per statement, in the order of the files.

    Returns:
        A pair ``(merged, skipped)``: the transactions without duplicates and the number of
        transactions that were dropped as duplicates. ``len(merged) + skipped`` always equals
        the number of transactions in all ``batches`` together.

    Requirements:
        * the result keeps the order of ``batches`` and, inside a batch, the original order
        * only the first transaction with a given ``id`` is kept; later ones are dropped
          and counted in ``skipped`` (this also applies to duplicates inside a single batch)
        * an empty ``batches`` list, or only empty batches, give ``([], 0)``
        * the input lists are not modified, and a new list is always returned
    """

    seen_ids: set[str] = set()
    merged: list[Transaction] = []
    skipped = 0

    for batch in batches:
        for transaction in batch:
            if transaction.id not in seen_ids:
                merged.append(transaction)
                seen_ids.add(transaction.id)
            else:
                skipped += 1

    return merged, skipped
