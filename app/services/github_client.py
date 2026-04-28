from __future__ import annotations

from datetime import date, timedelta

from app.models import ContributionDay


class GitHubClient:
    """GitHub contributions の取得クライアント（現状スタブ）。"""

    def get_contributions(
        self,
        username: str,
        start_date: date,
        end_date: date,
    ) -> list[ContributionDay]:
        # TODO: GraphQL contributionsCollection で実装
        days: list[ContributionDay] = []
        cursor = start_date

        while cursor <= end_date:
            # スタブとして擬似的な件数を生成
            pseudo_count = (hash(f"{username}:{cursor.isoformat()}") % 15)
            days.append(ContributionDay(date=cursor, count=pseudo_count))
            cursor += timedelta(days=1)

        return days
