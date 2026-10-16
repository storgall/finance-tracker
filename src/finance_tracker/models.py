from dataclasses import dataclass
from datetime import date as Date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    """A single bank transaction."""

    id: str
    date: Date
    amount: Decimal
    counterparty: str
    description: str

    @property
    def is_expense(self) -> bool:
        return self.amount < 0


@dataclass()
class Transactions:
    """The transactions of an import together with what was left out of them."""

    transactions: list[Transaction]
    skipped: int
    """How many transactions were dropped as duplicates of an earlier one (same ``id``)."""
    ignored: int
    """How many transactions were removed because they match an ignore keyword."""


@dataclass()
class Overview:
    """A summary of transactions by category."""

    expenses: dict[str, Decimal]
    income: dict[str, Decimal]

    def add(self, expense: bool, category: str, amount: Decimal) -> None:
        if expense:
            self.expenses[category] = self.expenses.get(category, Decimal("0.00")) + amount
        else:
            self.income[category] = self.income.get(category, Decimal("0.00")) + amount

    def sort(self) -> None:
        self.expenses = dict(sorted(self.expenses.items(), key=lambda item: item[1], reverse=False))
        self.income = dict(sorted(self.income.items(), key=lambda item: item[1], reverse=True))

    @property
    def total_expenses(self) -> Decimal:
        return sum(self.expenses.values(), Decimal("0.00"))

    @property
    def total_income(self) -> Decimal:
        return sum(self.income.values(), Decimal("0.00"))

    @property
    def net_total(self) -> Decimal:
        return self.total_income + self.total_expenses
