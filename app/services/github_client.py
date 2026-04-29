from __future__ import annotations

import logging
import time
from datetime import date, datetime, time as dt_time, timezone

import httpx

from app.exceptions import ExternalServiceError
from app.models import ContributionDay

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub GraphQL API から contribution を取得するクライアント。"""

    API_URL = "https://api.github.com/graphql"
    MAX_RETRIES = 3
    BACKOFF_BASE_SECONDS = 0.5

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
            "from": datetime.combine(start_date, dt_time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "to": datetime.combine(end_date, dt_time.max, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                payload = self._post_graphql(client, query=query, variables=variables)
        except (httpx.HTTPError, ValueError) as exc:
            raise ExternalServiceError(f"GitHub API request failed: {exc}") from exc

        errors = payload.get("errors", [])
        if errors:
            logger.warning("github_graphql_errors", extra={"username": username, "errors": errors})

        user = payload.get("data", {}).get("user")
        if not user:
            error_message = errors[0].get("message") if errors else f"GitHub user not found: {username}"
            raise ExternalServiceError(f"GitHub GraphQL response missing user data: {error_message}")

        weeks = user.get("contributionsCollection", {}).get("contributionCalendar", {}).get("weeks", [])

        days: list[ContributionDay] = []
        for week in weeks:
            for day in week.get("contributionDays", []):
                day_date = date.fromisoformat(day["date"])
                if start_date <= day_date <= end_date:
                    days.append(ContributionDay(date=day_date, count=day["contributionCount"]))

        days.sort(key=lambda item: item.date)
        return days

    def _post_graphql(self, client: httpx.Client, query: str, variables: dict) -> dict:
        last_exc: Exception | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = client.post(
                    self.API_URL,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    },
                    json={"query": query, "variables": variables},
                )
                if response.status_code == 429 or response.status_code == 403 or 500 <= response.status_code < 600:
                    if attempt == self.MAX_RETRIES:
                        response.raise_for_status()
                    logger.warning("github_graphql_retryable_status", extra={"status": response.status_code, "attempt": attempt})
                    time.sleep(self.BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt == self.MAX_RETRIES:
                    raise
                logger.warning("github_graphql_retryable_exception", extra={"attempt": attempt, "error": str(exc)})
                time.sleep(self.BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))

        assert last_exc is not None
        raise last_exc
