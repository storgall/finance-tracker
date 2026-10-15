import tomllib
from pathlib import Path

type Rules = dict[str, list[str]]
"""Category name -> keywords. Insertion order is the priority order."""


def load_rules(path: Path) -> Rules:
    """Load categorization rules from a TOML file.

    Expected file layout (the order of the lines is the priority order)::

        [rules]
        Groceries = ["albert", "billa"]
        Rent = ["nájem"]

    Returns:
        A ``Rules`` dict: category name -> list of keywords, in file order.
        An empty ``[rules]`` table is valid and returns ``{}``.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        ValueError: with a message starting with ``"Failed to parse"`` if the file is not
            valid TOML; or if the ``[rules]`` table is missing / is not a table; or if the
            keywords of a category are not a list of strings (the message names the
            category).
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
        if not isinstance(keywords, list) or not all(
            isinstance(keyword, str) for keyword in keywords
        ):
            raise ValueError(
                f"Invalid keywords for category '{category}': must be a list of strings"
            )

    return rules
