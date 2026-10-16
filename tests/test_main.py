from importlib.metadata import version
from pathlib import Path

import pytest

from finance_tracker import main

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE = FIXTURES / "sample_statement.xml"
FIXTURE_2 = FIXTURES / "sample_statement_2.xml"
RULES = FIXTURES / "rules.toml"


def test_import_prints_number_of_transactions(capsys: pytest.CaptureFixture[str]) -> None:
    main(["import", str(FIXTURE), "--rules", str(RULES)])

    assert "Imported 4 transactions" in capsys.readouterr().out.splitlines()


def test_import_prints_income_and_expenses_overview(capsys: pytest.CaptureFixture[str]) -> None:
    main(["import", str(FIXTURE), "--rules", str(RULES)])

    assert capsys.readouterr().out.splitlines() == [
        "Imported 4 transactions",
        "Date range: 2026-09-03 to 2026-09-21",
        "",
        "Total Income: 25000.00",
        "Total Expenses: 12225.49",
        "Net Total: 12774.51",
        "",
        "Income:",
        "  Uncategorized: 25000.00",
        "",
        "Expenses:",
        "  Rent: 12000.00",
        "  Groceries: 125.50",
        "  Streaming: 99.99",
    ]


def test_import_missing_rules_file_reports_error_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["import", str(FIXTURE), "--rules", str(tmp_path / "no_rules.toml")])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert captured.err.startswith("Error:")


def test_import_without_rules_option_uses_data_rules_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "rules.toml").write_text('[rules]\nRent = ["nájem"]\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    main(["import", str(FIXTURE)])

    assert "  Rent: 12000.00" in capsys.readouterr().out.splitlines()


def test_import_without_rules_option_and_without_default_file_fails_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["import", str(FIXTURE)])

    assert exc_info.value.code == 1
    assert "rules" in capsys.readouterr().err


def test_import_invalid_rules_file_reports_error_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad_rules = tmp_path / "rules.toml"
    bad_rules.write_text('[rules]\nGroceries = "market"\n', encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["import", str(FIXTURE), "--rules", str(bad_rules)])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "Groceries" in captured.err


def test_missing_command_exits_with_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 2
    assert "usage: finance-tracker" in capsys.readouterr().err


def test_import_without_path_exits_with_usage_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["import"])

    assert exc_info.value.code == 2


def test_import_missing_file_reports_error_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["import", str(tmp_path / "does_not_exist.xml")])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert captured.err.startswith("Error:")
    assert captured.out == ""


def test_import_malformed_xml_reports_error_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken = tmp_path / "broken.xml"
    broken.write_text("<statement><transactions>", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["import", str(broken)])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "Failed to parse XML" in captured.err
    assert captured.out == ""


def test_import_statement_without_transactions_prints_zero_totals_and_no_date_range(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    empty = tmp_path / "empty.xml"
    empty.write_text("<statement><transactions/></statement>", encoding="utf-8")

    main(["import", str(empty), "--rules", str(RULES)])

    lines = capsys.readouterr().out.splitlines()
    assert "Imported 0 transactions" in lines
    assert not any(line.startswith("Date range") for line in lines)
    assert "Total Income: 0.00" in lines
    assert "Total Expenses: 0.00" in lines
    assert "Net Total: 0.00" in lines


def test_version_option_prints_installed_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"finance-tracker {version('finance-tracker')}"


def test_import_several_files_merges_transactions_and_skips_duplicates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["import", str(FIXTURE), str(FIXTURE_2), "--rules", str(RULES)])

    assert capsys.readouterr().out.splitlines() == [
        "Imported 5 transactions",
        "Skipped 1 duplicate transactions",
        "Date range: 2026-09-03 to 2026-10-02",
        "",
        "Total Income: 25000.00",
        "Total Expenses: 12275.49",
        "Net Total: 12724.51",
        "",
        "Income:",
        "  Uncategorized: 25000.00",
        "",
        "Expenses:",
        "  Rent: 12000.00",
        "  Groceries: 125.50",
        "  Streaming: 99.99",
        "  Uncategorized: 50.00",
    ]


def test_import_same_file_twice_counts_every_transaction_once(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["import", str(FIXTURE), str(FIXTURE), "--rules", str(RULES)])

    lines = capsys.readouterr().out.splitlines()
    assert "Imported 4 transactions" in lines
    assert "Skipped 4 duplicate transactions" in lines
    assert "Total Expenses: 12225.49" in lines


def test_import_single_file_does_not_mention_duplicates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["import", str(FIXTURE), "--rules", str(RULES)])

    assert "Skipped" not in capsys.readouterr().out


def test_import_stops_with_error_when_one_of_several_files_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["import", str(FIXTURE), str(tmp_path / "missing.xml"), "--rules", str(RULES)])

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "missing.xml" in captured.err
    assert captured.out == ""
