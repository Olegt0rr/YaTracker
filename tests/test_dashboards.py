"""Tests for the dashboards category and its structs.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/dashboards/create-dashboard
https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

The masked numeric ids from the doc samples (``11********``) are not valid
JSON, so they are replaced here with concrete digits while keeping every
other field verbatim.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from yatracker.types.dashboard import CycleTimeWidget, Dashboard, WidgetBucket
from yatracker.types.status import Status

from tests.conftest import make_tracker, sent_json, user_ref

BASE = "https://api.tracker.yandex.net/v3"

# POST /v3/dashboards/ response sample.
CREATE_DASHBOARD_RESPONSE: dict[str, Any] = {
    "id": 10,
    "version": 1,
    "name": "New Dashboard",
    "createdBy": user_ref(
        self="https://api.tracker.yandex.net/v3/users/1187654321",
        id="1187654321",
        display="Имя Фамилия",
        cloudUid="ajeppa7dgp531187654321",
        passportUid=1187654321,
    ),
    "createdAt": "2024-04-15T19:38:42.074+0000",
    "layout": "one-column",
    "owner": user_ref(
        self="https://api.tracker.yandex.net/v3/users/1187654321",
        id="1187654321",
        display="Имя Фамилия",
        cloudUid="ajeppa7dgp531187654321",
        passportUid=1187654321,
    ),
    "self": "https://api.tracker.yandex.net/v3/dashboards/10",
}

# POST /v3/dashboards/<id>/widgets/cycleTime response sample.
WIDGET_RESPONSE: dict[str, Any] = {
    "id": 123456,
    "version": 1,
    "createdBy": user_ref(
        self="https://api.tracker.yandex.net/v3/users/1187654321",
        id="1187654321",
        display="Имя Фамилия",
        cloudUid="ajeppa7dgp531187654321",
        passportUid=1187654321,
    ),
    "description": "My widget",
    "color": 0,
    "dashboard": {
        "self": "https://api.tracker.yandex.net/v3/dashboards/118899",
        "id": "118899",
        "display": "My dashboard",
    },
    "fromStatuses": [
        {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        },
    ],
    "toStatuses": [
        {
            "self": "https://api.tracker.yandex.net/v3/statuses/3",
            "id": "3",
            "key": "resolved",
            "display": "Решен",
        },
    ],
    "bucket": {"type": "days", "count": 2},
    "calendar": {"id": "1", "display": "Moscow, 11:00−20:00"},
    "query": "Queue: TEST Assignee: me()",
    "datasetInfo": {
        "status": "created",
        "buildStartedAt": "2024-04-15T20:58:07.957+0000",
        "builtBy": user_ref(
            self="https://api.tracker.yandex.net/v3/users/1187654321",
            id="1187654321",
            display="Имя Фамилия",
            cloudUid="ajeppa7dgp531187654321",
            passportUid=1187654321,
        ),
    },
    "lines": {
        "standardDeviation": True,
        "movingAverage": True,
        "percentile": [83.0, 90.0, 75.0],
        "cakePercentile": 85.0,
    },
    "start": "now()-2w",
    "end": "now()-2d",
    "mode": "common-lines-and-points",
    "self": "https://api.tracker.yandex.net/v3/widgets/123456",
}


# --- create_dashboard --------------------------------------------------


async def test_create_dashboard_sends_name_only() -> None:
    tracker, client = make_tracker(CREATE_DASHBOARD_RESPONSE, status=201)
    dashboard = await tracker.create_dashboard("New Dashboard")

    assert isinstance(dashboard, Dashboard)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/dashboards/"
    assert sent_json(call) == {"name": "New Dashboard"}


async def test_create_dashboard_sends_layout() -> None:
    tracker, client = make_tracker(CREATE_DASHBOARD_RESPONSE, status=201)
    await tracker.create_dashboard("New Dashboard", layout="two-columns")

    assert sent_json(client.calls[0]) == {
        "name": "New Dashboard",
        "layout": "two-columns",
    }


async def test_create_dashboard_wraps_scalar_owner() -> None:
    tracker, client = make_tracker(CREATE_DASHBOARD_RESPONSE, status=201)
    await tracker.create_dashboard("New Dashboard", owner="username1")

    assert sent_json(client.calls[0]) == {
        "name": "New Dashboard",
        "owner": {"id": "username1"},
    }


async def test_create_dashboard_wraps_int_owner_id() -> None:
    tracker, client = make_tracker(CREATE_DASHBOARD_RESPONSE, status=201)
    await tracker.create_dashboard("New Dashboard", owner=1234567890)

    assert sent_json(client.calls[0])["owner"] == {"id": "1234567890"}


async def test_create_dashboard_keeps_dict_owner_as_is() -> None:
    tracker, client = make_tracker(CREATE_DASHBOARD_RESPONSE, status=201)
    await tracker.create_dashboard("New Dashboard", owner={"id": "username1"})

    assert sent_json(client.calls[0])["owner"] == {"id": "username1"}


async def test_create_dashboard_decodes_response() -> None:
    tracker, _ = make_tracker(CREATE_DASHBOARD_RESPONSE, status=201)
    dashboard = await tracker.create_dashboard("New Dashboard")

    assert dashboard.id == "10"
    assert dashboard.version == 1
    assert dashboard.name == "New Dashboard"
    assert dashboard.created_by.display == "Имя Фамилия"
    assert dashboard.created_at == datetime(
        2024,
        4,
        15,
        19,
        38,
        42,
        74000,
        tzinfo=timezone.utc,
    )
    assert dashboard.layout == "one-column"
    assert dashboard.owner is not None
    assert dashboard.owner.id == "1187654321"
    assert dashboard.url == "https://api.tracker.yandex.net/v3/dashboards/10"


# --- create_cycle_time_widget -------------------------------------------


async def test_create_cycle_time_widget_sends_description_only() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    widget = await tracker.create_cycle_time_widget(10, "My widget")

    assert isinstance(widget, CycleTimeWidget)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/dashboards/10/widgets/cycleTime"
    assert sent_json(call) == {"description": "My widget"}


async def test_create_cycle_time_widget_sends_full_body_with_string_statuses() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    await tracker.create_cycle_time_widget(
        10,
        "My widget",
        query="Assignee: username1@",
        filter_={"queue": "TEST", "assignee": "username2"},
        filter_id=1234,
        from_statuses=["open"],
        to_statuses=["closed"],
        excluded_statuses=["blocked"],
        included_statuses=["verified"],
        bucket={"unit": "days", "count": 1},
        calendar=123,
        lines={
            "movingAverage": True,
            "standardDeviation": True,
            "percentile": [75, 83, 90],
            "cakePercentile": 85,
        },
        start="now()-2w",
        end="now()-2d",
        mode="common-lines",
        auto_updatable=True,
    )

    assert sent_json(client.calls[0]) == {
        "description": "My widget",
        "query": "Assignee: username1@",
        "filter": {"queue": "TEST", "assignee": "username2"},
        "filterId": 1234,
        "fromStatuses": [{"key": "open"}],
        "toStatuses": [{"key": "closed"}],
        "excludedStatuses": [{"key": "blocked"}],
        "includedStatuses": [{"key": "verified"}],
        "bucket": {"unit": "days", "count": 1},
        "calendar": 123,
        "lines": {
            "movingAverage": True,
            "standardDeviation": True,
            "percentile": [75, 83, 90],
            "cakePercentile": 85,
        },
        "start": "now()-2w",
        "end": "now()-2d",
        "mode": "common-lines",
        "autoUpdatable": True,
    }


async def test_create_cycle_time_widget_accepts_status_objects_and_dicts() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    status = Status(url="s", id="1", key="open", display="Открыт")
    await tracker.create_cycle_time_widget(
        10,
        "My widget",
        from_statuses=[status],
        to_statuses=[{"key": "closed"}],
    )

    payload = sent_json(client.calls[0])
    assert payload["fromStatuses"] == [{"key": "open"}]
    assert payload["toStatuses"] == [{"key": "closed"}]


async def test_create_cycle_time_widget_passes_kwargs() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    await tracker.create_cycle_time_widget(10, "My widget", custom_field="value")

    assert sent_json(client.calls[0])["customField"] == "value"


async def test_create_cycle_time_widget_excludes_dashboard_id_from_body() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    await tracker.create_cycle_time_widget(10, "My widget")

    payload = sent_json(client.calls[0])
    assert "dashboardId" not in payload
    assert "dashboard_id" not in payload


async def test_create_cycle_time_widget_decodes_response() -> None:
    tracker, _ = make_tracker(WIDGET_RESPONSE, status=201)
    widget = await tracker.create_cycle_time_widget(10, "My widget")

    assert widget.id == "123456"
    assert widget.version == 1
    assert widget.description == "My widget"
    assert widget.color == 0
    assert widget.dashboard is not None
    assert widget.dashboard.display == "My dashboard"
    assert widget.from_statuses is not None
    assert widget.from_statuses[0].key == "open"
    assert widget.to_statuses is not None
    assert widget.to_statuses[0].key == "resolved"
    assert widget.bucket is not None
    assert widget.bucket.type == "days"
    assert widget.bucket.count == 2
    assert widget.calendar is not None
    assert widget.calendar.id == "1"
    assert widget.query == "Queue: TEST Assignee: me()"
    assert widget.dataset_info is not None
    assert widget.dataset_info.status == "created"
    assert widget.dataset_info.built_by is not None
    assert widget.dataset_info.built_by.display == "Имя Фамилия"
    assert widget.lines is not None
    assert widget.lines.percentile == [83.0, 90.0, 75.0]
    assert widget.lines.cake_percentile == 85.0
    assert widget.start == "now()-2w"
    assert widget.end == "now()-2d"
    assert widget.mode == "common-lines-and-points"
    assert widget.url == "https://api.tracker.yandex.net/v3/widgets/123456"


async def test_create_cycle_time_widget_rejects_bare_status() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    bare_statuses: list[Any] = [
        "open",
        {"key": "open"},
        Status(url="s", id="1", key="open", display="Открыт"),
    ]
    for bare in bare_statuses:
        with pytest.raises(TypeError, match="sequence of statuses"):
            await tracker.create_cycle_time_widget(10, "My widget", from_statuses=bare)

    assert client.calls == []


async def test_create_cycle_time_widget_names_the_offending_param() -> None:
    tracker, _ = make_tracker(WIDGET_RESPONSE, status=201)
    with pytest.raises(TypeError, match="`excluded_statuses`"):
        await tracker.create_cycle_time_widget(
            10,
            "My widget",
            excluded_statuses="open",  # type: ignore[arg-type]
        )


async def test_create_cycle_time_widget_accepts_a_tuple_of_statuses() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    await tracker.create_cycle_time_widget(
        10,
        "My widget",
        from_statuses=("open", "inProgress"),
    )

    assert sent_json(client.calls[0])["fromStatuses"] == [
        {"key": "open"},
        {"key": "inProgress"},
    ]


async def test_create_cycle_time_widget_renames_bucket_model_type_to_unit() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    widget = await tracker.create_cycle_time_widget(10, "My widget")
    assert widget.bucket is not None

    await tracker.create_cycle_time_widget(10, "Copy", bucket=widget.bucket)

    assert sent_json(client.calls[1])["bucket"] == {"unit": "days", "count": 2}


async def test_create_cycle_time_widget_sends_sprints_bucket_board_id() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    await tracker.create_cycle_time_widget(
        10,
        "My widget",
        bucket=WidgetBucket(type="sprints", count=1, board_id="123"),
    )

    assert sent_json(client.calls[0])["bucket"] == {
        "unit": "sprints",
        "count": 1,
        "boardId": "123",
    }


async def test_create_cycle_time_widget_keeps_dict_bucket_as_is() -> None:
    tracker, client = make_tracker(WIDGET_RESPONSE, status=201)
    await tracker.create_cycle_time_widget(
        10,
        "My widget",
        bucket={"unit": "weeks", "count": 3},
    )

    assert sent_json(client.calls[0])["bucket"] == {"unit": "weeks", "count": 3}
