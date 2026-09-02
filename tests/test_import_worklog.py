"""Tests for `Imports.import_worklog`.

Payload taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/import/import-worklogs

The masked numeric ids from the doc sample (``80***************``) are not
valid JSON, so they are replaced here with concrete digits while keeping
every other field verbatim.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from yatracker import YaTracker
from yatracker.types.worklog import Worklog

from tests.conftest import FakeClient, sent_json

BASE = "https://api.tracker.yandex.net/v3"

CREATED_AT = datetime(2025, 2, 18, 16, 35, 41, 740000, tzinfo=timezone.utc)
# the API documents `YYYY-MM-DDThh:mm:ss.sss±hhmm` — no colon in the offset
CREATED_AT_ISO = "2025-02-18T16:35:41.740+0000"

# POST /v3/issues/<id>/worklogs/_import response sample.
WORKLOG_RESPONSE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/ISSUE-1/worklog/37",
    "id": 37,
    "version": 1,
    "issue": {
        "self": "https://api.tracker.yandex.net/v3/issues/ISSUE-1",
        "id": "66e412345678901234567890",
        "key": "ISSUE-1",
        "display": "My issue 1",
    },
    "comment": "My comment",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/8012345678901234",
        "id": "8012345678901234",
        "display": "Username",
        "cloudUid": "aj12345678901234",
        "passportUid": 1961234567,
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/8012345678901234",
        "id": "8012345678901234",
        "display": "Username",
        "cloudUid": "aj12345678901234",
        "passportUid": 1961234567,
    },
    "createdAt": "2025-02-18T16:35:41.740+0000",
    "updatedAt": "2025-02-18T16:35:41.740+0000",
    "start": "2025-02-18T16:35:41.740+0000",
    "duration": "P1DT1H",
}


def _client() -> FakeClient:
    return FakeClient(body=json.dumps(WORKLOG_RESPONSE).encode())


async def test_import_worklog_request() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    worklog = await tracker.import_worklog(
        "ISSUE-1",
        duration="PT1H",
        created_at=CREATED_AT,
        created_by="username",
        start=CREATED_AT,
    )

    assert isinstance(worklog, Worklog)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/issues/ISSUE-1/worklogs/_import"
    assert sent_json(call) == {
        "duration": "PT1H",
        "createdAt": CREATED_AT_ISO,
        "createdBy": "username",
        "start": CREATED_AT_ISO,
    }


async def test_import_worklog_with_comment_and_int_author() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    await tracker.import_worklog(
        "ISSUE-1",
        duration="PT1H",
        created_at=CREATED_AT,
        created_by=1234,
        start=CREATED_AT,
        comment="My comment",
    )

    payload = sent_json(client.calls[0])
    assert payload["comment"] == "My comment"
    assert payload["createdBy"] == 1234
    assert "issue_id" not in payload
    assert "issueId" not in payload


async def test_import_worklog_passes_kwargs() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    await tracker.import_worklog(
        "ISSUE-1",
        duration="P6W",
        created_at=CREATED_AT,
        created_by="username",
        start=CREATED_AT,
        custom_field="value",
    )

    payload = sent_json(client.calls[0])
    assert payload["duration"] == "P6W"
    assert payload["customField"] == "value"


async def test_import_worklog_passes_str_timestamps_verbatim() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    await tracker.import_worklog(
        "ISSUE-1",
        duration="PT1H",
        created_at="2025-02-18T16:35:41.740+0300",
        created_by="username",
        start="2025-02-18T10:00:00.000+0300",
    )

    payload = sent_json(client.calls[0])
    assert payload["createdAt"] == "2025-02-18T16:35:41.740+0300"
    assert payload["start"] == "2025-02-18T10:00:00.000+0300"


async def test_import_worklog_formats_non_utc_offset() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    moscow = timezone(timedelta(hours=3))
    await tracker.import_worklog(
        "ISSUE-1",
        duration="PT1H",
        created_at=datetime(2025, 2, 18, 19, 35, 41, 7000, tzinfo=moscow),
        created_by="username",
        start=datetime(2025, 2, 18, 19, 0, 0, tzinfo=moscow),
    )

    payload = sent_json(client.calls[0])
    assert payload["createdAt"] == "2025-02-18T19:35:41.007+0300"
    assert payload["start"] == "2025-02-18T19:00:00.000+0300"


async def test_import_worklog_warns_on_naive_created_at() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    with pytest.warns(UserWarning, match="naive datetime") as record:
        await tracker.import_worklog(
            "ISSUE-1",
            duration="PT1H",
            created_at=datetime(2025, 2, 18, 16, 35, 41, 740000),  # noqa: DTZ001
            created_by="username",
            start=CREATED_AT,
        )

    assert sent_json(client.calls[0])["createdAt"] == "2025-02-18T16:35:41.740"
    # the warning must point at the caller, not at library internals
    assert record[0].filename == __file__


async def test_import_worklog_warns_on_naive_start() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    with pytest.warns(UserWarning, match="naive datetime") as record:
        await tracker.import_worklog(
            "ISSUE-1",
            duration="PT1H",
            created_at=CREATED_AT,
            created_by="username",
            start=datetime(2025, 2, 18, 16, 35, 41, 740000),  # noqa: DTZ001
        )

    assert sent_json(client.calls[0])["start"] == "2025-02-18T16:35:41.740"
    assert record[0].filename == __file__


async def test_import_worklog_decodes_response() -> None:
    client = _client()
    tracker = YaTracker(client=client)
    worklog = await tracker.import_worklog(
        "ISSUE-1",
        duration="PT1H",
        created_at=CREATED_AT,
        created_by="username",
        start=CREATED_AT,
    )

    assert worklog.id == 37
    assert worklog.version == 1
    assert worklog.issue.key == "ISSUE-1"
    assert worklog.issue.display == "My issue 1"
    assert worklog.comment == "My comment"
    assert worklog.created_by.display == "Username"
    assert worklog.updated_by is not None
    assert worklog.updated_by.display == "Username"
    assert worklog.created_at == CREATED_AT
    assert worklog.updated_at == CREATED_AT
    assert worklog.start == CREATED_AT
    assert worklog.duration == "P1DT1H"
    assert worklog.url == "https://api.tracker.yandex.net/v3/issues/ISSUE-1/worklog/37"
