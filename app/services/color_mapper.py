from __future__ import annotations

from app.models import ContributionLevel

# Google Calendar colorId の一例。
# 本番では colors.get API で実際に使用可能な色IDを確認して上書きする想定。
LEVEL_TO_COLOR_ID: dict[ContributionLevel, str] = {
    0: "8",   # gray
    1: "2",   # light green
    2: "10",  # green
    3: "9",   # dark green
    4: "11",  # darkest green
}


def to_level(count: int) -> ContributionLevel:
    if count <= 0:
        return 0
    if count <= 3:
        return 1
    if count <= 7:
        return 2
    if count <= 12:
        return 3
    return 4


def to_color_id(count: int) -> str:
    return LEVEL_TO_COLOR_ID[to_level(count)]
