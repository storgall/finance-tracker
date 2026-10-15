import pytest

from finance_tracker import main


def test_main_prints_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    assert "finance-tracker" in capsys.readouterr().out
