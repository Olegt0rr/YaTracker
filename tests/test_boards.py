"""Tests for the boards category and the `Board`/`BoardColumn` structs.

Payloads are taken from the official documentation:
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards-paginate
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board
https://yandex.cloud/ru/docs/tracker/concepts/boards/post-board
https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-board
https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-board
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-columns
https://yandex.cloud/ru/docs/tracker/concepts/boards/get-column
https://yandex.cloud/ru/docs/tracker/concepts/boards/post-column
https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-column
https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-column
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types import Board, BoardColumn, BoardColumnParams

from tests.conftest import USER, FakeClient, make_tracker, sent_json

# GET /boards, GET /boards/{id}, POST /liveBoards/, PATCH /boards/{id} response shape.
BOARD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/boards/1",
    "id": 1,
    "version": 1,
    "name": "My board",
    "createdAt": "2026-01-22T09:02:18.647+0000",
    "updatedAt": "2026-01-22T09:02:18.647+0000",
    "createdBy": USER,
    "columns": [
        {
            "self": "https://api.tracker.yandex.net/v3/boards/1/columns/1",
            "id": "1",
            "display": "Открыт",
        },
    ],
    "useRanking": False,
    "estimateBy": {
        "self": "https://api.tracker.yandex.net/v3/fields/storyPoints",
        "id": "storyPoints",
        "display": "Story Points",
    },
    "country": {
        "self": "https://api.tracker.yandex.net/v3/countries/1",
        "id": "1",
        "display": "Россия",
    },
    "calendar": {"id": 6},
}

# Minimal board payload: no deprecated/optional fields.
MINIMAL_BOARD: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/boards/2",
    "id": 2,
    "version": 1,
    "name": "Bare board",
    "createdAt": "2026-01-22T09:02:18.647+0000",
    "createdBy": USER,
}

# GET/POST/PATCH board column response shape.
BOARD_COLUMN: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/boards/73/columns/1",
    "id": 1,
    "name": "Открыт",
    "statuses": [
        {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        },
    ],
}


class TestBoardDecoding:
    def test_full_response_decodes(self) -> None:
        board = TypeAdapter(Board).validate_json(json.dumps(BOARD))
        assert board.id == "1"
        assert board.version == 1
        assert board.name == "My board"
        assert board.created_at == datetime(
            2026,
            1,
            22,
            9,
            2,
            18,
            647000,
            tzinfo=timezone.utc,
        )
        assert board.updated_at == board.created_at
        assert board.created_by.display == "Имя Фамилия"
        assert board.columns is not None
        assert board.columns[0].id == "1"
        assert board.columns[0].display == "Открыт"
        assert board.use_ranking is False
        assert board.estimate_by is not None
        assert board.estimate_by.id == "storyPoints"
        assert board.country is not None
        assert board.country.display == "Россия"
        assert board.calendar is not None
        # numeric calendar id coerced to str
        assert board.calendar.id == "6"

    def test_minimal_response_decodes_without_optionals(self) -> None:
        board = TypeAdapter(Board).validate_json(json.dumps(MINIMAL_BOARD))
        assert board.id == "2"
        assert board.updated_at is None
        assert board.columns is None
        assert board.use_ranking is None
        assert board.estimate_by is None
        assert board.country is None
        assert board.calendar is None
        assert board.auto_filter_settings is None

    def test_auto_filter_settings_kept_as_dict(self) -> None:
        payload = {
            **MINIMAL_BOARD,
            "autoFilterSettings": {
                "addFilterSettings": {"enabled": True},
                "removeFilterSettings": {"enabled": False},
            },
        }
        board = TypeAdapter(Board).validate_json(json.dumps(payload))
        assert board.auto_filter_settings == {
            "addFilterSettings": {"enabled": True},
            "removeFilterSettings": {"enabled": False},
        }


class TestBoardColumnDecoding:
    def test_column_decodes(self) -> None:
        column = TypeAdapter(BoardColumn).validate_json(json.dumps(BOARD_COLUMN))
        assert column.id == "1"
        assert column.name == "Открыт"
        assert column.statuses is not None
        assert column.statuses[0].id == "1"
        assert column.statuses[0].key == "open"
        assert column.statuses[0].display == "Открыт"


class TestBoardEndpoints:
    async def test_get_boards_decodes_list(self) -> None:
        tracker, client = make_tracker([BOARD])
        boards = await tracker.get_boards()
        assert len(boards) == 1
        assert boards[0].name == "My board"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/boards")
        assert call["params"] is None

    async def test_get_boards_paginated_passes_params(self) -> None:
        tracker, client = make_tracker([BOARD])
        boards = await tracker.get_boards_paginated(per_page=20, id_=5)
        assert len(boards) == 1

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/boards/_paginate")
        assert call["params"] == {"perPage": "20", "id": "5"}

    async def test_get_boards_paginated_without_args_sends_no_params(self) -> None:
        tracker, client = make_tracker([BOARD])
        await tracker.get_boards_paginated()
        assert client.calls[0]["params"] is None

    async def test_get_board_uses_board_path(self) -> None:
        tracker, client = make_tracker(BOARD)
        board = await tracker.get_board(1)
        assert board.name == "My board"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/boards/1")

    async def test_iter_boards_walks_pages_and_stops_on_empty(self) -> None:
        board_1 = {**BOARD, "id": 1}
        board_2 = {**BOARD, "id": 2}
        client = FakeClient(
            responses=[
                (200, json.dumps([board_1, board_2]).encode(), {}),
                (200, b"[]", {}),
            ],
        )
        tracker = YaTracker(client=client)

        boards = [board async for board in tracker.iter_boards(per_page=2)]

        assert [b.id for b in boards] == ["1", "2"]
        assert len(client.calls) == 2
        # first call: no `id` cursor
        assert client.calls[0]["params"] == {"perPage": "2"}
        # second call: id of the last board from the first page
        assert client.calls[1]["params"] == {"perPage": "2", "id": "2"}

    async def test_iter_boards_stops_immediately_on_empty_first_page(self) -> None:
        client = FakeClient(responses=[(200, b"[]", {})])
        tracker = YaTracker(client=client)

        boards = [board async for board in tracker.iter_boards()]

        assert boards == []
        assert len(client.calls) == 1

    async def test_create_board_sends_live_boards_endpoint(self) -> None:
        tracker, client = make_tracker(BOARD, status=201)
        board = await tracker.create_board("My board")
        assert board.id == "1"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/liveBoards/")
        assert sent_json(call) == {"name": "My board"}

    async def test_create_board_sends_full_body_with_camel_case_keys(self) -> None:
        tracker, client = make_tracker(BOARD, status=201)
        await tracker.create_board(
            "My board",
            owner="username",
            board_permissions_template="private",
            backlog_available=True,
            sprints_available=True,
            columns=[BoardColumnParams(name="To Do", statuses=["new", "open"])],
            backlog_columns=[BoardColumnParams(name="Later", limit=5)],
            non_parametrized_columns=[BoardColumnParams(name="Ideas", limit=5)],
            auto_filters={
                "addFilter": {
                    "liveFilter": {
                        "fieldValues": {
                            "queue": [{"fixed": "DEV"}],
                            "assignee": [{"fixed": "username"}],
                        },
                    },
                    "enabled": True,
                },
                "removeFilter": {
                    "statuses": ["closed"],
                    "checkResolutionPresence": True,
                    "maxTimeInToRemoveState": "P6W",
                    "enabled": True,
                },
            },
        )

        assert sent_json(client.calls[0]) == {
            "name": "My board",
            "owner": "username",
            "boardPermissionsTemplate": "private",
            "backlogAvailable": True,
            "sprintsAvailable": True,
            "columns": [{"name": "To Do", "statuses": ["new", "open"]}],
            "backlogColumns": [{"name": "Later", "limit": 5}],
            "nonParametrizedColumns": [{"name": "Ideas", "limit": 5}],
            "autoFilters": {
                "addFilter": {
                    "liveFilter": {
                        "fieldValues": {
                            "queue": [{"fixed": "DEV"}],
                            "assignee": [{"fixed": "username"}],
                        },
                    },
                    "enabled": True,
                },
                "removeFilter": {
                    "statuses": ["closed"],
                    "checkResolutionPresence": True,
                    "maxTimeInToRemoveState": "P6W",
                    "enabled": True,
                },
            },
        }

    async def test_update_board_omits_board_id_and_version_from_body(self) -> None:
        tracker, client = make_tracker(BOARD)
        board = await tracker.update_board(5, version=3, name="Renamed board")
        assert board.id == "1"

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/boards/5")
        assert sent_json(call) == {"name": "Renamed board"}
        assert call["headers"] == {"If-Match": '"3"'}

    async def test_update_board_without_version_sends_no_headers(self) -> None:
        tracker, client = make_tracker(BOARD)
        await tracker.update_board(5, name="Renamed board")

        call = client.calls[0]
        assert call.get("headers") is None

    async def test_delete_board_returns_true(self) -> None:
        client = FakeClient(status=204, body=b"")
        tracker = YaTracker(client=client)
        assert await tracker.delete_board(1) is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/boards/1")


class TestBoardColumnEndpoints:
    async def test_get_board_columns_decodes_list(self) -> None:
        tracker, client = make_tracker([BOARD_COLUMN])
        columns = await tracker.get_board_columns(73)
        assert len(columns) == 1
        assert columns[0].statuses is not None
        assert columns[0].statuses[0].key == "open"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/boards/73/columns")

    async def test_get_board_column_uses_column_path(self) -> None:
        tracker, client = make_tracker(BOARD_COLUMN)
        column = await tracker.get_board_column(73, 1)
        assert column.name == "Открыт"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/boards/73/columns/1")

    async def test_create_board_column_sends_if_match_and_body(self) -> None:
        tracker, client = make_tracker(BOARD_COLUMN, status=201)
        column = await tracker.create_board_column(
            73,
            2,
            "Approve",
            ["needInfo"],
        )
        assert column.id == "1"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/boards/73/columns/")
        assert call["headers"] == {"If-Match": '"2"'}
        assert sent_json(call) == {"name": "Approve", "statuses": ["needInfo"]}

    async def test_update_board_column_sends_if_match_and_partial_body(self) -> None:
        tracker, client = make_tracker(BOARD_COLUMN)
        column = await tracker.update_board_column(73, 1, 2, name="Approved")
        assert column.name == "Открыт"

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/boards/73/columns/1")
        assert call["headers"] == {"If-Match": '"2"'}
        assert sent_json(call) == {"name": "Approved"}

    async def test_delete_board_column_sends_if_match_and_returns_true(self) -> None:
        client = FakeClient(status=204, body=b"")
        tracker = YaTracker(client=client)
        assert await tracker.delete_board_column(73, 1, 2) is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/boards/73/columns/1")
        assert call["headers"] == {"If-Match": '"2"'}


class TestBoardConvenienceMethods:
    async def test_board_get_columns_delegates_to_tracker(self) -> None:
        client = FakeClient(
            responses=[
                (200, json.dumps(BOARD).encode(), {}),
                (200, json.dumps([BOARD_COLUMN]).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        board = await tracker.get_board(1)
        columns = await board.get_columns()

        assert len(columns) == 1
        assert columns[0].name == "Открыт"
        assert len(client.calls) == 2
        assert client.calls[1]["url"].endswith("/boards/1/columns")

    async def test_board_get_sprints_delegates_to_tracker(self) -> None:
        sprint = {
            "self": "https://api.tracker.yandex.net/v3/sprints/4411",
            "id": 4411,
            "version": 1435288720018,
            "name": "Sprint 1",
            "board": {
                "self": "https://api.tracker.yandex.net/v3/boards/3",
                "id": "3",
                "display": "My board",
            },
            "status": "in_progress",
            "archived": False,
            "createdBy": USER,
            "createdAt": "2015-06-23T17:03:24.799+0000",
        }
        client = FakeClient(
            responses=[
                (200, json.dumps(BOARD).encode(), {}),
                (200, json.dumps([sprint]).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        board = await tracker.get_board(1)
        sprints = await board.get_sprints()

        assert len(sprints) == 1
        assert sprints[0].name == "Sprint 1"
        assert len(client.calls) == 2
        assert client.calls[1]["url"].endswith("/boards/1/sprints")
