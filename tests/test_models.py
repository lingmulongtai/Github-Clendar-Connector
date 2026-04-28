from datetime import date

import pytest
from pydantic import ValidationError

from app.models import SyncRequest


def test_sync_request_rejects_invalid_date_range() -> None:
    with pytest.raises(ValidationError):
        SyncRequest(
            github_username="octocat",
            calendar_id="primary",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 1),
        )
