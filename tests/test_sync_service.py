from datetime import date

from app.models import ContributionDay, SyncRequest
from app.services.google_calendar_client import UpsertStats
from app.services.sync_service import SyncService


class DummyGitHubClient:
    def get_contributions(self, username: str, start_date: date, end_date: date) -> list[ContributionDay]:
        _ = (username, start_date, end_date)
        return [
            ContributionDay(date=date(2026, 1, 1), count=0),
            ContributionDay(date=date(2026, 1, 2), count=5),
        ]


class DummyGoogleClient:
    def __init__(self) -> None:
        self.events = []
        self.dry_run = False

    def upsert_events(self, calendar_id: str, events: list, dry_run: bool = False) -> UpsertStats:
        _ = calendar_id
        self.events = events
        self.dry_run = dry_run
        return UpsertStats(created=len(events), updated=0)


def test_sync_skips_zero_days_when_disabled() -> None:
    google = DummyGoogleClient()
    service = SyncService(github_client=DummyGitHubClient(), google_client=google)

    result = service.sync(
        SyncRequest(
            github_username="octocat",
            calendar_id="primary",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            show_zero_days=False,
        )
    )

    assert result.synced_events == 1
    assert result.created_events == 1
    assert result.updated_events == 0
    assert result.skipped_days == 1
    assert len(google.events) == 1
    assert google.events[0].color_id == "10"


def test_sync_sets_dry_run() -> None:
    google = DummyGoogleClient()
    service = SyncService(github_client=DummyGitHubClient(), google_client=google)

    result = service.sync(
        SyncRequest(
            github_username="octocat",
            calendar_id="primary",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            dry_run=True,
        )
    )

    assert result.dry_run is True
    assert google.dry_run is True
