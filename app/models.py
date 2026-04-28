from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

ContributionLevel = Literal[0, 1, 2, 3, 4]


class SyncRequest(BaseModel):
    github_username: str = Field(min_length=1)
    calendar_id: str = Field(min_length=1)
    start_date: date
    end_date: date
    show_zero_days: bool = True


class ContributionDay(BaseModel):
    date: date
    count: int = Field(ge=0)


class CalendarEvent(BaseModel):
    external_id: str
    summary: str
    description: str
    start_date: date
    end_date: date
    color_id: str


class SyncResult(BaseModel):
    synced_events: int
    skipped_days: int
