from finance_tracker.models import Transaction, Transactions


def merge_transactions(batches: list[list[Transaction]]) -> Transactions:
    """Join transactions from several statements into one list without duplicates.

    Statements exported from the bank can overlap, so the same transaction (same ``id``)
    may appear in more than one batch.

    Args:
        batches: one list of transactions per statement, in the order of the files.

    Returns:
        A ``Transactions`` with the transactions without duplicates and ``skipped``, the
        number of transactions dropped as duplicates. ``ignored`` is always ``0`` here.
        ``len(result.transactions) + result.skipped`` equals the number of transactions in
        all ``batches`` together.

    Requirements:
        * the result keeps the order of ``batches`` and, inside a batch, the original order
        * only the first transaction with a given ``id`` is kept; later ones are dropped
          and counted in ``skipped`` (this also applies to duplicates inside a single batch)
        * an empty ``batches`` list, or only empty batches, give no transactions and
          ``skipped == 0``
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

    return Transactions(transactions=merged, skipped=skipped, ignored=0)
