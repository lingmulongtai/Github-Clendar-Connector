from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

import httpx

from app.exceptions import ExternalServiceError
from app.models import CalendarEvent

logger = logging.getLogger(__name__)


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
    MAX_RETRIES = 3
    BACKOFF_BASE_SECONDS = 0.5

    def __init__(self, access_token: str):
        self.access_token = access_token

    def upsert_events(self, calendar_id: str, events: list[CalendarEvent], dry_run: bool = False) -> UpsertStats:
        stats = UpsertStats()
        if not events:
            return stats

        encoded_calendar_id = quote(calendar_id, safe="")
        external_ids = [event.external_id for event in events]
        earliest_start = min(event.start_date for event in events)
        latest_end_exclusive = max(event.end_date for event in events)
        latest_end_inclusive = latest_end_exclusive if latest_end_exclusive > earliest_start else earliest_start

        try:
            with httpx.Client(timeout=15.0) as client:
                existing_by_external_id = self._fetch_existing_events_by_external_id(
                    client=client,
                    encoded_calendar_id=encoded_calendar_id,
                    external_ids=set(external_ids),
                    start_date=earliest_start,
                    end_date=latest_end_inclusive,
                )

                for event in events:
                    existing_id = existing_by_external_id.get(event.external_id)
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

        logger.info(
            "google_calendar_upsert_complete",
            extra={
                "total": stats.total,
                "created": stats.created,
                "updated": stats.updated,
                "dry_run": dry_run,
            },
        )
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

    def _request_with_retry(self, client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = client.request(
                    method,
                    url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    **kwargs,
                )
                status = response.status_code
                if status == 429 or 500 <= status < 600:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else self.BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                    if attempt == self.MAX_RETRIES:
                        response.raise_for_status()
                    logger.warning("google_calendar_retryable_status", extra={"status": status, "attempt": attempt})
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt == self.MAX_RETRIES:
                    raise
                delay = self.BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                logger.warning("google_calendar_retryable_exception", extra={"attempt": attempt, "error": str(exc)})
                time.sleep(delay)

        assert last_exc is not None
        raise last_exc

    def _patch_event(self, client: httpx.Client, encoded_calendar_id: str, event_id: str, event: CalendarEvent) -> None:
        encoded_event_id = quote(event_id, safe="")
        self._request_with_retry(
            client,
            "PATCH",
            f"{self.BASE_URL}/{encoded_calendar_id}/events/{encoded_event_id}",
            json=self._event_body(event),
        )

    def _create_event(self, client: httpx.Client, encoded_calendar_id: str, event: CalendarEvent) -> None:
        self._request_with_retry(
            client,
            "POST",
            f"{self.BASE_URL}/{encoded_calendar_id}/events",
            json=self._event_body(event),
        )

    def _fetch_existing_events_by_external_id(
        self,
        client: httpx.Client,
        encoded_calendar_id: str,
        external_ids: set[str],
        start_date: date,
        end_date: date,
    ) -> dict[str, str]:
        page_token: str | None = None
        results: dict[str, str] = {}

        while True:
            params = {
                "singleEvents": True,
                "timeMin": f"{start_date.isoformat()}T00:00:00Z",
                "timeMax": f"{end_date.isoformat()}T23:59:59Z",
                "maxResults": 250,
                "fields": "nextPageToken,items(id,extendedProperties/private/externalId)",
            }
            if page_token:
                params["pageToken"] = page_token

            response = self._request_with_retry(
                client,
                "GET",
                f"{self.BASE_URL}/{encoded_calendar_id}/events",
                params=params,
            )
            payload = response.json()
            for item in payload.get("items", []):
                external_id = item.get("extendedProperties", {}).get("private", {}).get("externalId")
                event_id = item.get("id")
                if external_id and event_id and external_id in external_ids:
                    results[external_id] = event_id

            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        return results
