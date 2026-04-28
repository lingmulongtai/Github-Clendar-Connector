import os

import pytest

from app.core.settings import Settings
from app.exceptions import ConfigurationError


def test_require_tokens_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    monkeypatch.setenv("GOOGLE_ACCESS_TOKEN", "ya29_test")

    github_token, google_token = Settings.from_env().require_tokens()

    assert github_token == "ghp_test"
    assert google_token == "ya29_test"


def test_require_tokens_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_ACCESS_TOKEN", raising=False)

    with pytest.raises(ConfigurationError):
        Settings.from_env().require_tokens()

    # Avoid side effects in some runners
    os.environ.pop("GITHUB_TOKEN", None)
    os.environ.pop("GOOGLE_ACCESS_TOKEN", None)
