from __future__ import annotations

import os
from dataclasses import dataclass

from app.exceptions import ConfigurationError


@dataclass(frozen=True)
class Settings:
    github_token: str | None
    google_access_token: str | None

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            github_token=os.getenv("GITHUB_TOKEN"),
            google_access_token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        )

    def require_tokens(self) -> tuple[str, str]:
        if not self.github_token:
            raise ConfigurationError("Missing environment variable: GITHUB_TOKEN")
        if not self.google_access_token:
            raise ConfigurationError("Missing environment variable: GOOGLE_ACCESS_TOKEN")
        return self.github_token, self.google_access_token
