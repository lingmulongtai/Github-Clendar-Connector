from __future__ import annotations

from app.models import CalendarEvent


class GoogleCalendarClient:
    """Google Calendar 書き込みクライアント（現状スタブ）。"""

    def upsert_events(self, calendar_id: str, events: list[CalendarEvent]) -> int:
        # TODO: events.insert / events.patch + extendedProperties.private.externalId で本実装
        # 現在は「書き込みに成功した体」で件数のみ返す。
        _ = calendar_id
        return len(events)
