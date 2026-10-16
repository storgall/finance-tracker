from finance_tracker.models import Overview, Transaction, Transactions
from finance_tracker.periods import period_key
from finance_tracker.rules import Rules

UNCATEGORIZED = "Uncategorized"


def categorize_transactions(transactions: list[Transaction], rules: Rules) -> Overview:
    result: Overview = Overview(expenses={}, income={})
    for transaction in transactions:
        expense = transaction.is_expense
        category = categorize(transaction, rules)
        result.add(expense, category, transaction.amount)

    result.sort()
    return result


def categorize_by_period(
    transactions: list[Transaction], rules: Rules, granularity: str
) -> dict[str, Overview]:
    """Split ``transactions`` into periods and build an ``Overview`` of each period.

    Args:
        transactions: the transactions to summarize, in any order.
        rules: the categorization rules, as in ``categorize_transactions``.
        granularity: one of ``periods.GRANULARITIES``; the label of a period is given by
            ``periods.period_key``.

    Returns:
        A dict from the period label to the ``Overview`` of the transactions of that period,
        with the periods in chronological order.

    Raises:
        ValueError: if ``granularity`` is not supported and there is a transaction to place.

    Requirements:
        * every period gets exactly the overview ``categorize_transactions`` would give for
          its own transactions
        * a period without transactions is not in the result; no transactions give ``{}``
        * the order of the input does not matter and the input list is not modified
    """

    transactions_by_period: dict[str, list[Transaction]] = {}

    for transaction in transactions:
        transactions_by_period.setdefault(period_key(transaction.date, granularity), []).append(
            transaction
        )

    return {
        label: categorize_transactions(transactions_by_period[label], rules)
        for label in sorted(transactions_by_period)
    }


def categorize(transaction: Transaction, rules: Rules) -> str:
    """Return the category of ``transaction`` according to ``rules``.

    ``rules`` maps a category name to a list of keywords, e.g.
    ``{"Groceries": ["market", "albert"], "Rent": ["nájem"]}``.

    A rule matches when at least one of its keywords occurs anywhere in the
    transaction's ``counterparty`` or ``description``.

    Requirements:
        * matching ignores letter case (``"market"`` matches ``"TEST MARKET"``)
        * the first matching rule wins; rules are tried in the order of ``rules``
        * if no rule matches (or ``rules`` is empty), return ``UNCATEGORIZED``
        * empty and whitespace-only keywords never match, otherwise they would match
          (almost) everything
        * the amount is ignored: income and expenses are categorized the same way
    """

    for category, keywords in rules.items():
        if _matches(transaction, keywords):
            return category
    return UNCATEGORIZED


def remove_ignored(transactions: Transactions, ignore_keywords: list[str]) -> Transactions:
    """Remove the transactions that match any of the ignore keywords.

    Args:
        transactions: the imported transactions. The object is changed in place.
        ignore_keywords: keywords matched with the same rules as in ``is_ignored``.

    Returns:
        The same ``transactions`` object, without the ignored ones. Its ``ignored`` field is
        set to the number of removed transactions; ``skipped`` is left untouched. With no
        keywords nothing is removed.
    """

    if not ignore_keywords:
        return transactions

    num_transactions = len(transactions.transactions)
    transactions.transactions = [
        t for t in transactions.transactions if not is_ignored(t, ignore_keywords)
    ]
    transactions.ignored = num_transactions - len(transactions.transactions)

    return transactions


def is_ignored(transaction: Transaction, keywords: list[str]) -> bool:
    """Tell whether ``transaction`` must be left out of the overview.

    A transaction is ignored when at least one of ``keywords`` occurs anywhere in its
    ``counterparty`` or ``description``, for example the number of a savings account.

    Requirements:
        * the matching rules are the same as in ``categorize``: letter case is ignored and
          empty or whitespace-only keywords never match
        * an empty ``keywords`` list ignores nothing
        * the amount is irrelevant: income and expenses are treated the same way
    """
    return _matches(transaction, keywords)


def _matches(transaction: Transaction, keywords: list[str]) -> bool:
    """Tell whether any of ``keywords`` occurs in the counterparty or description.

    Shared by ``categorize`` and ``is_ignored``, so that both match in exactly the same way.

    Requirements:
        * letter case is ignored
        * empty and whitespace-only keywords never match
    """

    text = f"{transaction.counterparty} {transaction.description}".casefold()

    return any(keyword.casefold() in text for keyword in keywords if keyword.strip())
