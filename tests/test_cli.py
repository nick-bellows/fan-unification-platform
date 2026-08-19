import pytest

from fanuni import __version__
from fanuni.cli import main


def test_info_prints_version_and_no_secrets(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["info"]) == 0
    out = capsys.readouterr().out
    assert __version__ in out
    assert "database_url" in out
    assert "dev-local-token" not in out
    assert "minioadmin" not in out


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
