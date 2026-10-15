import xml.etree.ElementTree as ET
from datetime import date as Date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from finance_tracker.models import Transaction


def parse_statement(path: Path) -> list[Transaction]:
    """Read a Moneta XML statement and return its transactions in file order.

    Each ``statement/transactions/transaction`` element becomes one ``Transaction``:
        date:         attribute ``date-eff`` (ISO ``YYYY-MM-DD``)
        amount:       attribute ``amount`` as ``Decimal`` (signed, dot decimal separator)
        counterparty: attribute ``other-account-number`` (empty string if missing)
        description:  texts of all ``trn-message`` elements inside
                      ``trn-messages[@type='description']``, joined with a single space
                      (empty string if there are none)

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: if the file is not well-formed XML, or if a transaction lacks the
            ``date-eff`` or ``amount`` attribute.
    """
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}") from e

    return [
        _parse_transaction(transaction)
        for transaction in root.findall("./transactions/transaction")
    ]


def _parse_transaction(transaction: ET.Element) -> Transaction:
    date = Date.fromisoformat(_required(transaction, "date-eff"))
    amount_str = _required(transaction, "amount")
    try:
        amount = Decimal(amount_str)
    except InvalidOperation as e:
        raise ValueError(f"Invalid amount in transaction: {amount_str}") from e
    counterparty = transaction.get("other-account-number", "")
    description = _get_description(transaction)

    return Transaction(date, amount, counterparty, description)


def _get_description(transaction: ET.Element) -> str:
    texts = []
    for messages in transaction.findall("trn-messages"):
        if messages.get("type") != "description":
            continue
        for message in messages.findall("trn-message"):
            if message.text:
                texts.append(message.text)

    return " ".join(texts)


def _required(transaction: ET.Element, key: str) -> str:
    value = transaction.get(key)
    if value is None:
        raise ValueError(f"Missing required attribute '{key}'")
    return value
