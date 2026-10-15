from finance_tracker.models import Overview, Transaction
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

    text = f"{transaction.counterparty} {transaction.description}".casefold()

    for category, keywords in rules.items():
        if any(keyword.casefold() in text for keyword in keywords if keyword.strip()):
            return category
    return UNCATEGORIZED
