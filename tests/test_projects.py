"""Tests for the projects category and the `Project` struct.

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/projects/get-projects
https://yandex.ru/support/tracker/ru/api/projects/get-project
https://yandex.ru/support/tracker/ru/api/projects/create-project
https://yandex.ru/support/tracker/ru/api/projects/update-project
https://yandex.ru/support/tracker/ru/api/projects/delete-project
https://yandex.ru/support/tracker/ru/api/projects/get-project-queues
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types import FullQueue
from yatracker.types.project import Project

from tests.conftest import (
    USER,
    FakeClient,
    full_queue_body,
    make_tracker,
    sent_json,
)

# `GET /projects/{id}` response.
PROJECT: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/projects/9",
    "id": "9",
    "version": 1,
    "key": "Project",
    "name": "Project",
    "description": "My project",
    "lead": USER,
    "status": "launched",
    "startDate": "2020-11-16",
    "endDate": "2020-12-16",
}

# A project without any optional field, as the API answers for a freshly
# created draft.
MINIMAL_PROJECT: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/projects/9",
    # the field table types `id` as a number, examples show a string
    "id": 9,
    "version": 1,
    "key": "Project",
    "name": "Project",
}

# `PUT /projects/{id}` response: the version is bumped.
UPDATED_PROJECT: dict[str, Any] = {**PROJECT, "version": 2}


class TestProjectDecoding:
    def test_full_response_decodes(self) -> None:
        project = TypeAdapter(Project).validate_json(json.dumps(PROJECT))
        assert project.url.endswith("/projects/9")
        assert project.id == "9"
        assert project.version == 1
        assert project.key == "Project"
        assert project.name == "Project"
        assert project.description == "My project"
        assert project.lead is not None
        assert project.lead.display == "Имя Фамилия"
        assert project.status == "launched"
        assert project.start_date == date(2020, 11, 16)
        assert project.end_date == date(2020, 12, 16)

    def test_minimal_response_decodes_without_optionals(self) -> None:
        project = TypeAdapter(Project).validate_json(json.dumps(MINIMAL_PROJECT))
        # the API may send a number, `Base` coerces it to a string
        assert project.id == "9"
        assert project.description is None
        assert project.lead is None
        assert project.status is None
        assert project.start_date is None
        assert project.end_date is None
        assert project.team_users is None
        assert project.team_groups is None
        assert project.queues is None

    def test_expand_queues_decodes_full_queues(self) -> None:
        payload = {**PROJECT, "queues": [full_queue_body()]}
        project = TypeAdapter(Project).validate_json(json.dumps(payload))
        assert project.queues is not None
        assert project.queues[0].key == "TEST"

    def test_undocumented_team_fields_decode(self) -> None:
        payload = {
            **PROJECT,
            "teamUsers": [USER],
            "teamGroups": [{"id": 1, "display": "Group"}],
        }
        project = TypeAdapter(Project).validate_json(json.dumps(payload))
        assert project.team_users is not None
        assert project.team_users[0].id == "1111"
        assert project.team_groups == [{"id": 1, "display": "Group"}]


class TestProjectEndpoints:
    async def test_get_projects_decodes_list(self) -> None:
        tracker, client = make_tracker([PROJECT])
        projects = await tracker.get_projects()
        assert len(projects) == 1
        assert projects[0].name == "Project"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/projects")
        assert call["params"] is None

    async def test_get_projects_passes_expand(self) -> None:
        tracker, client = make_tracker([PROJECT])
        await tracker.get_projects(expand="queues")

        assert client.calls[0]["params"] == {"expand": "queues"}

    async def test_get_project_uses_id_in_path(self) -> None:
        tracker, client = make_tracker(PROJECT)
        project = await tracker.get_project(9)
        assert project.id == "9"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/projects/9")
        assert call["params"] is None

    async def test_get_project_passes_expand(self) -> None:
        tracker, client = make_tracker(PROJECT)
        await tracker.get_project("9", expand="queues")

        assert client.calls[0]["params"] == {"expand": "queues"}

    async def test_create_project_sends_camel_case_body(self) -> None:
        tracker, client = make_tracker(PROJECT)
        project = await tracker.create_project("Project", ["TEST"])
        assert project.id == "9"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/projects")
        assert call["params"] is None
        # `None` fields are omitted
        assert sent_json(call) == {"name": "Project", "queues": ["TEST"]}

    async def test_create_project_renders_dates(self) -> None:
        tracker, client = make_tracker(PROJECT)
        await tracker.create_project(
            "Project",
            "TEST",
            description="My project",
            lead="artem",
            status="LAUNCHED",
            start_date=date(2020, 11, 16),
            end_date="2020-12-16",
        )

        # a string `queues` is sent as is, dates are rendered as YYYY-MM-DD
        assert sent_json(client.calls[0]) == {
            "name": "Project",
            "queues": "TEST",
            "description": "My project",
            "lead": "artem",
            "status": "LAUNCHED",
            "startDate": "2020-11-16",
            "endDate": "2020-12-16",
        }

    async def test_update_project_puts_with_version_param(self) -> None:
        tracker, client = make_tracker(UPDATED_PROJECT)
        project = await tracker.update_project(9, 1, ["TEST"])
        assert project.version == 2

        call = client.calls[0]
        assert call["method"] == "PUT"
        assert call["url"].endswith("/projects/9")
        assert call["params"] == {"version": "1"}
        # neither `project_id`, `version` nor `expand` leak into the body
        assert sent_json(call) == {"queues": ["TEST"]}

    async def test_update_project_passes_expand_and_fields(self) -> None:
        tracker, client = make_tracker(UPDATED_PROJECT)
        await tracker.update_project(
            "9",
            "1",
            ["TEST", "ORG"],
            name="Project",
            description="My project",
            lead=1111,
            status="IN_PROGRESS",
            start_date=date(2020, 11, 16),
            end_date=date(2020, 12, 16),
            expand="queues",
        )

        call = client.calls[0]
        assert call["params"] == {"version": "1", "expand": "queues"}
        assert sent_json(call) == {
            "queues": ["TEST", "ORG"],
            "name": "Project",
            "description": "My project",
            "lead": 1111,
            "status": "IN_PROGRESS",
            "startDate": "2020-11-16",
            "endDate": "2020-12-16",
        }

    async def test_delete_project_returns_none(self) -> None:
        client = FakeClient(body=b"", status=204)
        tracker = YaTracker(client=client)
        assert await tracker.delete_project(9) is None

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/projects/9")
        assert call["data"] is None

    async def test_get_project_queues_decodes_queues(self) -> None:
        tracker, client = make_tracker([full_queue_body()])
        queues = await tracker.get_project_queues(9)
        assert isinstance(queues[0], FullQueue)
        assert queues[0].key == "TEST"

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/projects/9/queues")
        assert call["params"] is None

    async def test_get_project_queues_passes_expand(self) -> None:
        tracker, client = make_tracker([full_queue_body()])
        await tracker.get_project_queues("9", expand="all")

        assert client.calls[0]["params"] == {"expand": "all"}


class TestProjectHelpers:
    async def test_project_is_returned_with_tracker_attached(self) -> None:
        tracker, _ = make_tracker(PROJECT)
        project = await tracker.get_project(9)

        assert project._tracker is tracker

    async def test_get_queues_helper(self) -> None:
        client = FakeClient(
            responses=[
                (200, json.dumps(PROJECT).encode(), {}),
                (200, json.dumps([full_queue_body()]).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        project = await tracker.get_project(9)

        queues = await project.get_queues(expand="all")
        assert queues[0].key == "TEST"

        call = client.calls[1]
        assert call["method"] == "GET"
        assert call["url"].endswith("/projects/9/queues")
        assert call["params"] == {"expand": "all"}

    async def test_delete_helper(self) -> None:
        client = FakeClient(
            responses=[
                (200, json.dumps(PROJECT).encode(), {}),
                (204, b"", {}),
            ],
        )
        tracker = YaTracker(client=client)
        project = await tracker.get_project(9)

        assert await project.delete() is None

        call = client.calls[1]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/projects/9")
