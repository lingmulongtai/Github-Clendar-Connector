from __future__ import annotations

from datetime import date

import httpx

from app.exceptions import ExternalServiceError
from app.models import ContributionDay


class GitHubClient:
    """GitHub GraphQL API から contribution を取得するクライアント。"""

    API_URL = "https://api.github.com/graphql"

    def __init__(self, token: str):
        self.token = token

    def get_contributions(
        self,
        username: str,
        start_date: date,
        end_date: date,
    ) -> list[ContributionDay]:
        query = """
        query($username: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $username) {
            contributionsCollection(from: $from, to: $to) {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            "username": username,
            "from": f"{start_date.isoformat()}T00:00:00Z",
            "to": f"{end_date.isoformat()}T23:59:59Z",
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    json={"query": query, "variables": variables},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ExternalServiceError(f"GitHub API request failed: {exc}") from exc

        if payload.get("errors"):
            raise ExternalServiceError(f"GitHub GraphQL error: {payload['errors']}")

        user = payload.get("data", {}).get("user")
        if not user:
            raise ExternalServiceError(f"GitHub user not found: {username}")

        weeks = (
            user.get("contributionsCollection", {})
            .get("contributionCalendar", {})
            .get("weeks", [])
        )

        days: list[ContributionDay] = []
        for week in weeks:
            for d in week.get("contributionDays", []):
                day_date = date.fromisoformat(d["date"])
                if start_date <= day_date <= end_date:
                    days.append(ContributionDay(date=day_date, count=d["contributionCount"]))

        days.sort(key=lambda item: item.date)
        return days
