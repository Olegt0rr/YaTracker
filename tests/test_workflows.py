"""Tests for the workflows category and the `FullWorkflow`/`Workflow` structs.

Payloads are taken verbatim from the official documentation:
https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflows
https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflow
https://yandex.ru/support/tracker/ru/api/queues/workflows/post-workflow
https://yandex.ru/support/tracker/ru/api/queues/workflows/patch-workflow
https://yandex.ru/support/tracker/ru/api/queues/workflows/patch-workflow-action
https://yandex.ru/support/tracker/ru/api/queues/workflows/delete-workflow
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import TypeAdapter
from yatracker.types.workflow import FullWorkflow, Workflow

from tests.conftest import make_tracker, sent_json

# GET /workflows and GET /workflows/<id> response shape (identical sample on
# both doc pages).
FULL_WORKFLOW: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/workflows/W21",
    "id": "W21",
    "name": "Design",
    "version": 1,
    "steps": [
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "key": "open",
                "display": "Открыт",
            },
            "actions": [
                {
                    "id": "inProgress",
                    "name": "Взять в работу",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/3",
                        "id": "3",
                        "key": "inProgress",
                        "display": "В работе",
                    },
                },
            ],
        },
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/3",
                "id": "3",
                "key": "inProgress",
                "display": "В работе",
            },
            "actions": [
                {
                    "id": "close",
                    "name": "Закрыть",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/8",
                        "id": "8",
                        "key": "closed",
                        "display": "Закрыт",
                    },
                },
            ],
        },
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/8",
                "id": "8",
                "key": "closed",
                "display": "Закрыт",
            },
        },
    ],
    "initialAction": {
        "id": "open",
        "name": "Открыть",
        "target": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        },
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
        "id": "4",
        "key": "DESIGN",
        "display": "DESIGN",
    },
    "created": "2026-08-11T14:37:06.356+0000",
    "updated": "2026-08-11T14:37:06.356+0000",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "deleted": False,
    "type": "visual",
}

# POST /workflows request body, taken verbatim from the doc page.
POST_WORKFLOW_BODY: dict[str, Any] = {
    "name": "Design",
    "queue": "DESIGN",
    "type": "VISUAL",
    "initialAction": {
        "id": "open",
        "name": {"ru": "Открыть", "en": "Open"},
        "target": "open",
    },
    "steps": [
        {
            "status": "open",
            "description": {"ru": "Задача открыта", "en": "Issue is open"},
            "actions": [
                {
                    "id": "inProgress",
                    "name": {"ru": "Взять в работу", "en": "Start progress"},
                    "description": {
                        "ru": "Перевести задачу в работу",
                        "en": "Move issue to in progress",
                    },
                    "target": "inProgress",
                },
            ],
        },
        {
            "status": "inProgress",
            "description": {"ru": "Задача в работе", "en": "Issue is in progress"},
            "actions": [
                {
                    "id": "close",
                    "name": {"ru": "Закрыть", "en": "Close"},
                    "description": {"ru": "Закрыть задачу", "en": "Close the issue"},
                    "target": "closed",
                },
            ],
        },
        {
            "status": "closed",
            "description": {"ru": "Задача закрыта", "en": "Issue is closed"},
            "actions": [],
        },
    ],
    "issueTypeResolutions": [
        {
            "issueType": "task",
            "resolutions": ["wontFix", "fixed"],
        },
    ],
}

# POST /workflows response: minimal sample from the doc page (a single step,
# no `description`/`metaAction`/`statusType` echoed back).
POST_WORKFLOW_RESPONSE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/workflows/W21",
    "id": "W21",
    "name": "Design",
    "version": 1,
    "steps": [
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "key": "open",
                "display": "Открыт",
            },
            "actions": [
                {
                    "id": "inProgress",
                    "name": "Взять в работу",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/3",
                        "id": "3",
                        "key": "inProgress",
                        "display": "В работе",
                    },
                },
            ],
        },
    ],
    "initialAction": {
        "id": "open",
        "name": "Открыть",
        "target": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        },
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
        "id": "4",
        "key": "DESIGN",
        "display": "DESIGN",
    },
    "created": "2026-08-11T14:37:06.356+0000",
    "updated": "2026-08-11T14:37:06.356+0000",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "deleted": False,
    "type": "visual",
}

# PATCH /workflows/<id>?version=3 request body, taken verbatim from the
# worked example on the doc page.
PATCH_WORKFLOW_BODY: dict[str, Any] = {
    "name": "QA process",
    "initialAction": {
        "id": "new",
        "name": {"ru": "Создать", "en": "Create"},
        "target": "new",
    },
    "steps": [
        {
            "status": "new",
            "actions": [
                {
                    "id": "needInfo",
                    "name": {
                        "ru": "Отправить на тестирование",
                        "en": "Send to testing",
                    },
                    "target": "testing",
                },
            ],
        },
        {
            "status": "testing",
            "actions": [
                {
                    "id": "resolved",
                    "name": {"ru": "Завершить", "en": "Resolve"},
                    "target": "resolved",
                },
            ],
        },
        {
            "status": "resolved",
            "actions": [],
        },
    ],
}

# PATCH /workflows/<id>?version=3 response, taken verbatim from the doc page.
PATCH_WORKFLOW_RESPONSE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/workflows/W21",
    "id": "W21",
    "name": "Updated process",
    "version": 2,
    "steps": [
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "key": "open",
                "display": "Открыт",
            },
            "actions": [
                {
                    "id": "inProgress",
                    "name": "Взять в работу",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/3",
                        "id": "3",
                        "key": "inProgress",
                        "display": "В работе",
                    },
                },
            ],
        },
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/3",
                "id": "3",
                "key": "inProgress",
                "display": "В работе",
            },
            "actions": [
                {
                    "id": "close",
                    "name": "Закрыть",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/8",
                        "id": "8",
                        "key": "closed",
                        "display": "Закрыт",
                    },
                },
            ],
        },
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/8",
                "id": "8",
                "key": "closed",
                "display": "Закрыт",
            },
        },
    ],
    "initialAction": {
        "id": "open",
        "name": "Открыть",
        "target": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        },
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
        "id": "4",
        "key": "DESIGN",
        "display": "DESIGN",
    },
    "created": "2026-08-11T14:37:06.356+0000",
    "updated": "2026-08-11T15:10:00.000+0000",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "deleted": False,
    "type": "visual",
}

# PATCH /workflows/W21/steps/inProgress/actions/close?version=2 request body,
# taken verbatim from the worked example on the doc page.
PATCH_ACTION_BODY: dict[str, Any] = {
    "name": {"ru": "Завершить", "en": "Complete"},
    "description": {
        "ru": "Перевести задачу в статус «Закрыт»",
        "en": "Move issue to Closed status",
    },
    "target": "closed",
}

# Response of the same request, taken verbatim from the doc page.
PATCH_ACTION_RESPONSE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/workflows/W21",
    "id": "W21",
    "name": "Updated process",
    "version": 3,
    "steps": [
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/3",
                "id": "3",
                "key": "inProgress",
                "display": "В работе",
            },
            "actions": [
                {
                    "id": "close",
                    "name": "Закрыть",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/8",
                        "id": "8",
                        "key": "closed",
                        "display": "Закрыт",
                    },
                },
            ],
        },
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/8",
                "id": "8",
                "key": "closed",
                "display": "Закрыт",
            },
        },
        {
            "status": {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "key": "open",
                "display": "Открыт",
            },
            "actions": [
                {
                    "id": "inProgress",
                    "name": "Взять в работу",
                    "target": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/3",
                        "id": "3",
                        "key": "inProgress",
                        "display": "В работе",
                    },
                },
            ],
        },
    ],
    "initialAction": {
        "id": "open",
        "name": "Открыть",
        "target": {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        },
    },
    "queue": {
        "self": "https://api.tracker.yandex.net/v3/queues/DESIGN",
        "id": "4",
        "key": "DESIGN",
        "display": "DESIGN",
    },
    "created": "2026-08-12T12:42:50.675+0000",
    "updated": "2026-08-12T14:00:19.614+0000",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1100000000",
        "id": "1100000000",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1100000000,
    },
    "deleted": False,
    "type": "visual",
}


class TestWorkflowRefDecoding:
    """Short `Workflow` reference embedded into queue payloads."""

    def test_decodes_without_key(self) -> None:
        payload = {
            "self": "https://api.tracker.yandex.net/v3/workflows/W21",
            "id": "W21",
            "display": "Design",
        }
        workflow = TypeAdapter(Workflow).validate_json(json.dumps(payload))
        assert workflow.id == "W21"
        assert workflow.display == "Design"
        assert workflow.key is None

    def test_decodes_with_key(self) -> None:
        payload = {
            "self": "https://api.tracker.yandex.net/v3/workflows/W21",
            "id": "W21",
            "display": "Design",
            "key": "design",
        }
        workflow = TypeAdapter(Workflow).validate_json(json.dumps(payload))
        assert workflow.id == "W21"
        assert workflow.display == "Design"
        assert workflow.key == "design"


class TestFullWorkflowDecoding:
    def test_full_response_decodes(self) -> None:
        workflow = TypeAdapter(FullWorkflow).validate_json(json.dumps(FULL_WORKFLOW))
        assert workflow.id == "W21"
        assert workflow.name == "Design"
        assert workflow.version == 1
        assert len(workflow.steps) == 3

        first_step = workflow.steps[0]
        assert first_step.status.key == "open"
        assert first_step.actions is not None
        assert first_step.actions[0].id == "inProgress"
        assert first_step.actions[0].name == "Взять в работу"
        assert first_step.actions[0].target.key == "inProgress"
        assert first_step.actions[0].target.display == "В работе"

        # terminal step: the API omits `actions` entirely.
        terminal_step = workflow.steps[2]
        assert terminal_step.status.key == "closed"
        assert terminal_step.actions is None

        assert workflow.initial_action is not None
        assert workflow.initial_action.id == "open"
        assert workflow.initial_action.target.key == "open"

        assert workflow.queue is not None
        assert workflow.queue.key == "DESIGN"
        assert workflow.created == datetime(
            2026,
            8,
            11,
            14,
            37,
            6,
            356000,
            tzinfo=timezone.utc,
        )
        assert workflow.updated == workflow.created
        assert workflow.created_by is not None
        assert workflow.created_by.display == "Имя Фамилия"
        assert workflow.updated_by is not None
        assert workflow.updated_by.display == "Имя Фамилия"
        assert workflow.deleted is False
        assert workflow.type == "visual"

    def test_minimal_response_decodes(self) -> None:
        """Only `url`/`id`/`name`/`version`/`steps` are ever guaranteed."""
        payload = {
            "self": "https://api.tracker.yandex.net/v3/workflows/W21",
            "id": "W21",
            "name": "Design",
            "version": 1,
            "steps": [
                {
                    "status": {
                        "self": "https://api.tracker.yandex.net/v3/statuses/1",
                        "id": "1",
                        "key": "open",
                        "display": "Открыт",
                    },
                },
            ],
        }
        workflow = TypeAdapter(FullWorkflow).validate_json(json.dumps(payload))
        assert workflow.id == "W21"
        assert workflow.name == "Design"
        assert workflow.version == 1
        assert len(workflow.steps) == 1
        assert workflow.steps[0].actions is None
        assert workflow.initial_action is None
        assert workflow.queue is None
        assert workflow.created is None
        assert workflow.updated is None
        assert workflow.created_by is None
        assert workflow.updated_by is None
        assert workflow.deleted is None
        assert workflow.type is None


class TestGetWorkflows:
    async def test_get_workflows_uses_org_wide_path(self) -> None:
        tracker, client = make_tracker([FULL_WORKFLOW])
        workflows = await tracker.get_workflows()
        assert len(workflows) == 1
        assert workflows[0].id == "W21"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/workflows")
        assert call["params"] is None

    async def test_get_workflow_uses_id_path(self) -> None:
        tracker, client = make_tracker(FULL_WORKFLOW)
        workflow = await tracker.get_workflow("W21")
        assert workflow.name == "Design"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/workflows/W21")


class TestCreateWorkflow:
    async def test_sends_exact_body_from_docs(self) -> None:
        tracker, client = make_tracker(POST_WORKFLOW_RESPONSE, status=201)
        workflow = await tracker.create_workflow(
            "Design",
            {
                "id": "open",
                "name": {"ru": "Открыть", "en": "Open"},
                "target": "open",
            },
            [
                {
                    "status": "open",
                    "description": {"ru": "Задача открыта", "en": "Issue is open"},
                    "actions": [
                        {
                            "id": "inProgress",
                            "name": {"ru": "Взять в работу", "en": "Start progress"},
                            "description": {
                                "ru": "Перевести задачу в работу",
                                "en": "Move issue to in progress",
                            },
                            "target": "inProgress",
                        },
                    ],
                },
                {
                    "status": "inProgress",
                    "description": {
                        "ru": "Задача в работе",
                        "en": "Issue is in progress",
                    },
                    "actions": [
                        {
                            "id": "close",
                            "name": {"ru": "Закрыть", "en": "Close"},
                            "description": {
                                "ru": "Закрыть задачу",
                                "en": "Close the issue",
                            },
                            "target": "closed",
                        },
                    ],
                },
                {
                    "status": "closed",
                    "description": {"ru": "Задача закрыта", "en": "Issue is closed"},
                    "actions": [],
                },
            ],
            queue="DESIGN",
            type_="VISUAL",
            issue_type_resolutions=[
                {"issueType": "task", "resolutions": ["wontFix", "fixed"]},
            ],
        )
        assert workflow.id == "W21"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/workflows")
        assert sent_json(call) == POST_WORKFLOW_BODY

    async def test_minimal_call_sends_no_none_keys(self) -> None:
        tracker, client = make_tracker(POST_WORKFLOW_RESPONSE, status=201)
        await tracker.create_workflow(
            "Design",
            {"id": "open", "name": {"ru": "Открыть", "en": "Open"}, "target": "open"},
            [{"status": "open", "actions": []}],
        )

        assert sent_json(client.calls[0]) == {
            "name": "Design",
            "initialAction": {
                "id": "open",
                "name": {"ru": "Открыть", "en": "Open"},
                "target": "open",
            },
            "steps": [{"status": "open", "actions": []}],
        }

    async def test_id_is_sent_as_id(self) -> None:
        tracker, client = make_tracker(POST_WORKFLOW_RESPONSE, status=201)
        await tracker.create_workflow(
            "Design",
            {"id": "open", "name": {"ru": "Открыть", "en": "Open"}, "target": "open"},
            [{"status": "open", "actions": []}],
            id_="W99",
        )

        body = sent_json(client.calls[0])
        assert body["id"] == "W99"


class TestUpdateWorkflow:
    async def test_sends_version_as_query_param_and_exact_body(self) -> None:
        tracker, client = make_tracker(PATCH_WORKFLOW_RESPONSE)
        workflow = await tracker.update_workflow(
            "W21",
            3,
            name="QA process",
            initial_action={
                "id": "new",
                "name": {"ru": "Создать", "en": "Create"},
                "target": "new",
            },
            steps=[
                {
                    "status": "new",
                    "actions": [
                        {
                            "id": "needInfo",
                            "name": {
                                "ru": "Отправить на тестирование",
                                "en": "Send to testing",
                            },
                            "target": "testing",
                        },
                    ],
                },
                {
                    "status": "testing",
                    "actions": [
                        {
                            "id": "resolved",
                            "name": {"ru": "Завершить", "en": "Resolve"},
                            "target": "resolved",
                        },
                    ],
                },
                {"status": "resolved", "actions": []},
            ],
        )
        assert workflow.name == "Updated process"
        assert workflow.version == 2

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/workflows/W21")
        assert call["params"] == {"version": "3"}
        assert sent_json(call) == PATCH_WORKFLOW_BODY

    async def test_partial_update_sends_only_provided_fields(self) -> None:
        tracker, client = make_tracker(PATCH_WORKFLOW_RESPONSE)
        await tracker.update_workflow("W21", 2, name="Renamed")

        call = client.calls[0]
        assert call["params"] == {"version": "2"}
        assert sent_json(call) == {"name": "Renamed"}

    async def test_type_is_sent_as_type(self) -> None:
        tracker, client = make_tracker(PATCH_WORKFLOW_RESPONSE)
        await tracker.update_workflow("W21", 2, type_="VISUAL")

        assert sent_json(client.calls[0]) == {"type": "VISUAL"}


class TestUpdateWorkflowAction:
    async def test_sends_exact_path_params_and_body(self) -> None:
        tracker, client = make_tracker(PATCH_ACTION_RESPONSE)
        workflow = await tracker.update_workflow_action(
            "W21",
            "inProgress",
            "close",
            2,
            name={"ru": "Завершить", "en": "Complete"},
            description={
                "ru": "Перевести задачу в статус «Закрыт»",
                "en": "Move issue to Closed status",
            },
            target="closed",
        )
        assert workflow.version == 3

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/workflows/W21/steps/inProgress/actions/close")
        assert call["params"] == {"version": "2"}
        assert sent_json(call) == PATCH_ACTION_BODY

        # steps -> status -> actions -> target, drilled all the way down.
        first_step = workflow.steps[0]
        assert first_step.status.key == "inProgress"
        assert first_step.actions is not None
        assert first_step.actions[0].id == "close"
        assert first_step.actions[0].target.key == "closed"
        assert first_step.actions[0].target.display == "Закрыт"

    async def test_new_id_is_sent_as_id(self) -> None:
        tracker, client = make_tracker(PATCH_ACTION_RESPONSE)
        await tracker.update_workflow_action(
            "W21",
            "inProgress",
            "close",
            2,
            new_id="finish",
        )

        assert sent_json(client.calls[0]) == {"id": "finish"}

    async def test_minimal_call_sends_no_none_keys(self) -> None:
        tracker, client = make_tracker(PATCH_ACTION_RESPONSE)
        await tracker.update_workflow_action(
            "W21",
            "inProgress",
            "close",
            2,
            target="closed",
        )

        assert sent_json(client.calls[0]) == {"target": "closed"}


class TestDeleteWorkflow:
    async def test_delete_workflow_returns_true(self) -> None:
        tracker, client = make_tracker(status=204)
        assert await tracker.delete_workflow("W21") is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/workflows/W21")
