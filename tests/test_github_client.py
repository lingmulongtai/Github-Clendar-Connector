from datetime import date

import httpx
import pytest

from app.exceptions import ExternalServiceError
from app.services.github_client import GitHubClient


def _patch_client(transport: httpx.MockTransport):
    original = httpx.Client

    class ClientWithTransport(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    httpx.Client = ClientWithTransport  # type: ignore[assignment]
    return original


def test_get_contributions_recovers_when_errors_and_data_are_both_present() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": [{"contributionDays": [{"date": "2026-01-01", "contributionCount": 3}]}]}}}},
                "errors": [{"message": "partial failure"}],
            },
        )

    original = _patch_client(httpx.MockTransport(handler))
    try:
        days = GitHubClient("token").get_contributions("octocat", date(2026, 1, 1), date(2026, 1, 1))
    finally:
        httpx.Client = original  # type: ignore[assignment]

    assert len(days) == 1
    assert days[0].count == 3


def test_get_contributions_raises_when_user_data_missing() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"user": None}, "errors": [{"message": "not found"}]})

    original = _patch_client(httpx.MockTransport(handler))
    try:
        with pytest.raises(ExternalServiceError):
            GitHubClient("token").get_contributions("ghost", date(2026, 1, 1), date(2026, 1, 1))
    finally:
        httpx.Client = original  # type: ignore[assignment]
