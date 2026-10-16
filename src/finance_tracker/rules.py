import tomllib
from dataclasses import dataclass
from pathlib import Path

type Rules = dict[str, list[str]]
"""Category name -> keywords. Insertion order is the priority order."""


@dataclass(frozen=True)
class RuleSet:
    """Everything that is read from a rules file."""

    categories: Rules
    ignore: list[str]
    """Keywords of transactions that must not be counted at all (e.g. a savings account)."""


def load_rules(path: Path) -> RuleSet:
    """Load categorization rules from a TOML file.

    Expected file layout (the order of the lines is the priority order)::

        [rules]
        Groceries = ["albert", "billa"]
        Rent = ["nájem"]

        [ignore]
        keywords = ["123456789/0600"]

    The ``[rules]`` table is required. The ``[ignore]`` table, and its ``keywords`` list,
    are optional.

    Returns:
        A ``RuleSet``:

        * ``categories``: category name -> list of keywords, in file order. An empty
          ``[rules]`` table is valid and gives ``{}``.
        * ``ignore``: keywords of transactions to leave out of the overview; ``[]`` when the
          file has no ``[ignore]`` keywords.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: with a message starting with ``"Failed to parse"`` if the file is not
            valid TOML; if the ``[rules]`` table is missing or is not a table; if
            ``[ignore]`` is not a table; or if the keywords of a category, or the
            ``[ignore]`` keywords, are not a list of strings (the message names which).
    """
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Failed to parse TOML: {e}") from e

    rules = data.get("rules")
    if not isinstance(rules, dict):
        raise ValueError("Missing or invalid [rules] table")
    for category, keywords in rules.items():
        _validate_keywords(f"category '{category}'", keywords)

    ignore = data.get("ignore", {})
    if not isinstance(ignore, dict):
        raise ValueError("Invalid [ignore] table")
    ignore_keywords = ignore.get("keywords", [])
    _validate_keywords("[ignore] keywords", ignore_keywords)

    return RuleSet(categories=rules, ignore=ignore_keywords)


def _validate_keywords(where: str, keywords: object) -> None:
    """Check that ``keywords``, a value read from the file, is a list of strings.

    Args:
        where: describes the place in the file, used in the error message.
        keywords: the value to check; its type is unknown because it comes from TOML.

    Raises:
        ValueError: if ``keywords`` is not a list of strings.
    """
    if not isinstance(keywords, list) or not all(isinstance(keyword, str) for keyword in keywords):
        raise ValueError(f"Invalid keywords for {where}: must be a list of strings")
