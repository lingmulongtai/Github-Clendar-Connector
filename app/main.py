from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.core.settings import Settings
from app.exceptions import ConfigurationError, ExternalServiceError
from app.models import SyncRequest, SyncResult
from app.services.github_client import GitHubClient
from app.services.google_calendar_client import GoogleCalendarClient
from app.services.sync_service import SyncService

app = FastAPI(title="GitHub Calendar Connector", version="1.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sync", response_model=SyncResult)
def sync_contributions(req: SyncRequest) -> SyncResult:
    try:
        github_token, google_access_token = Settings.from_env().require_tokens()
        service = SyncService(
            github_client=GitHubClient(github_token),
            google_client=GoogleCalendarClient(google_access_token),
        )
        return service.sync(req)
    except ConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
