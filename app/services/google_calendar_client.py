from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.exceptions import ExternalServiceError
from app.models import CalendarEvent


@dataclass
class UpsertStats:
    created: int = 0
    updated: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated


class GoogleCalendarClient:
    """Google Calendar REST API へ upsert するクライアント。"""

    BASE_URL = "https://www.googleapis.com/calendar/v3/calendars"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def upsert_events(self, calendar_id: str, events: list[CalendarEvent], dry_run: bool = False) -> UpsertStats:
        stats = UpsertStats()
        if not events:
            return stats

        encoded_calendar_id = quote(calendar_id, safe="")

        try:
            with httpx.Client(timeout=15.0) as client:
                for event in events:
                    existing_id = self._find_existing_event_id(client, encoded_calendar_id, event.external_id)
                    if existing_id:
                        stats.updated += 1
                        if not dry_run:
                            self._patch_event(client, encoded_calendar_id, existing_id, event)
                    else:
                        stats.created += 1
                        if not dry_run:
                            self._create_event(client, encoded_calendar_id, event)
        except (httpx.HTTPError, ValueError) as exc:
            raise ExternalServiceError(f"Google Calendar API request failed: {exc}") from exc

        return stats

    def _event_body(self, event: CalendarEvent) -> dict:
        return {
            "summary": event.summary,
            "description": event.description,
            "start": {"date": event.start_date.isoformat()},
            "end": {"date": event.end_date.isoformat()},
            "colorId": event.color_id,
            "extendedProperties": {
                "private": {
                    "externalId": event.external_id,
                }
            },
        }

    def _patch_event(self, client: httpx.Client, encoded_calendar_id: str, event_id: str, event: CalendarEvent) -> None:
        encoded_event_id = quote(event_id, safe="")
        response = client.patch(
            f"{self.BASE_URL}/{encoded_calendar_id}/events/{encoded_event_id}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=self._event_body(event),
        )
        response.raise_for_status()

    def _create_event(self, client: httpx.Client, encoded_calendar_id: str, event: CalendarEvent) -> None:
        response = client.post(
            f"{self.BASE_URL}/{encoded_calendar_id}/events",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=self._event_body(event),
        )
        response.raise_for_status()

    def _find_existing_event_id(self, client: httpx.Client, encoded_calendar_id: str, external_id: str) -> str | None:
        response = client.get(
            f"{self.BASE_URL}/{encoded_calendar_id}/events",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={
                "privateExtendedProperty": f"externalId={external_id}",
                "maxResults": 1,
                "singleEvents": True,
                "fields": "items(id)",
            },
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return None
        return items[0].get("id")
