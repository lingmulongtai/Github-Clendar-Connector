from __future__ import annotations

from datetime import timedelta

from app.models import CalendarEvent, SyncRequest, SyncResult
from app.services.color_mapper import to_color_id
from app.services.github_client import GitHubClient
from app.services.google_calendar_client import GoogleCalendarClient


class SyncService:
    def __init__(self, github_client: GitHubClient, google_client: GoogleCalendarClient):
        self.github_client = github_client
        self.google_client = google_client

    def sync(self, req: SyncRequest) -> SyncResult:
        contribution_days = self.github_client.get_contributions(
            username=req.github_username,
            start_date=req.start_date,
            end_date=req.end_date,
        )

        events: list[CalendarEvent] = []
        skipped_days = 0

        for day in contribution_days:
            if day.count == 0 and not req.show_zero_days:
                skipped_days += 1
                continue

            events.append(
                CalendarEvent(
                    external_id=f"github:{req.github_username}:{day.date.isoformat()}",
                    summary=f"GitHub Contributions: {day.count}",
                    description=(
                        f"GitHub user: {req.github_username}\n"
                        f"Date: {day.date.isoformat()}\n"
                        f"Contributions: {day.count}"
                    ),
                    start_date=day.date,
                    end_date=day.date + timedelta(days=1),
                    color_id=to_color_id(day.count),
                )
            )

        stats = self.google_client.upsert_events(req.calendar_id, events, dry_run=req.dry_run)
        return SyncResult(
            synced_events=stats.total,
            skipped_days=skipped_days,
            created_events=stats.created,
            updated_events=stats.updated,
            dry_run=req.dry_run,
        )
