from __future__ import annotations

from datetime import timedelta

from fastapi import FastAPI, HTTPException

from app.models import CalendarEvent, SyncRequest, SyncResult
from app.services.color_mapper import to_color_id
from app.services.github_client import GitHubClient
from app.services.google_calendar_client import GoogleCalendarClient

app = FastAPI(title="GitHub Calendar Connector", version="0.1.0")


github_client = GitHubClient()
google_client = GoogleCalendarClient()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sync", response_model=SyncResult)
def sync_contributions(req: SyncRequest) -> SyncResult:
    if req.start_date > req.end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    contribution_days = github_client.get_contributions(
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

    synced_count = google_client.upsert_events(req.calendar_id, events)
    return SyncResult(synced_events=synced_count, skipped_days=skipped_days)
