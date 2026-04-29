from datetime import date

import httpx

from app.models import CalendarEvent
from app.services.google_calendar_client import GoogleCalendarClient


def _event(external_id: str, day: int) -> CalendarEvent:
    return CalendarEvent(
        external_id=external_id,
        summary="s",
        description="d",
        start_date=date(2026, 1, day),
        end_date=date(2026, 1, day + 1),
        color_id="1",
    )


def test_upsert_fetches_existing_events_once_and_updates_and_creates() -> None:
    requested_gets = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            requested_gets.append(str(request.url))
            return httpx.Response(200, json={"items": [{"id": "gcal-1", "extendedProperties": {"private": {"externalId": "a"}}}]})
        if request.method == "PATCH":
            return httpx.Response(200, json={})
        if request.method == "POST":
            return httpx.Response(200, json={})
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    original = httpx.Client

    class ClientWithTransport(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    httpx.Client = ClientWithTransport  # type: ignore[assignment]
    try:
        client = GoogleCalendarClient("token")
        stats = client.upsert_events("primary", [_event("a", 1), _event("b", 2)])
    finally:
        httpx.Client = original  # type: ignore[assignment]

    assert stats.created == 1
    assert stats.updated == 1
    assert len(requested_gets) == 1


def test_upsert_dry_run_does_not_write() -> None:
    methods = []

    def handler(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        if request.method == "GET":
            return httpx.Response(200, json={"items": []})
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    original = httpx.Client

    class ClientWithTransport(httpx.Client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    httpx.Client = ClientWithTransport  # type: ignore[assignment]
    try:
        client = GoogleCalendarClient("token")
        stats = client.upsert_events("primary", [_event("a", 1)], dry_run=True)
    finally:
        httpx.Client = original  # type: ignore[assignment]

    assert stats.created == 1
    assert methods == ["GET"]
