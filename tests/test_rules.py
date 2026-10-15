from pathlib import Path

import pytest

from finance_tracker.rules import load_rules

FIXTURE = Path(__file__).parent / "fixtures" / "rules.toml"


def write_toml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "rules.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_categories_and_keywords() -> None:
    rules = load_rules(FIXTURE)

    assert rules == {
        "Groceries": ["test market", "fake grocer"],
        "Rent": ["nájem"],
        "Streaming": ["fake streaming"],
    }


def test_keeps_file_order_as_priority() -> None:
    assert list(load_rules(FIXTURE)) == ["Groceries", "Rent", "Streaming"]


def test_empty_rules_table_returns_empty_dict(tmp_path: Path) -> None:
    assert load_rules(write_toml(tmp_path, "[rules]\n")) == {}


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_rules(tmp_path / "does_not_exist.toml")


def test_invalid_toml_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, "[rules\nGroceries = ")

    with pytest.raises(ValueError, match="Failed to parse"):
        load_rules(path)


def test_missing_rules_table_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, '[other]\nGroceries = ["market"]\n')

    with pytest.raises(ValueError, match="rules"):
        load_rules(path)


def test_rules_that_is_not_a_table_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, "rules = 5\n")

    with pytest.raises(ValueError, match="rules"):
        load_rules(path)


@pytest.mark.parametrize(
    "line",
    [
        'Groceries = "market"',  # a string instead of a list
        "Groceries = [1, 2]",  # a list of numbers
        'Groceries = ["market", 3]',  # one bad item is enough
    ],
)
def test_keywords_that_are_not_a_list_of_strings_raise_value_error(
    tmp_path: Path, line: str
) -> None:
    path = write_toml(tmp_path, f"[rules]\n{line}\n")

    with pytest.raises(ValueError, match="Groceries"):
        load_rules(path)
