from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from yatracker.tracker.base import BaseTracker
from yatracker.types import FullQueue, Project
from yatracker.utils.datetime import to_tracker_date

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import date

# ruff: noqa: PLR0913

QueueT_co = TypeVar("QueueT_co", bound=FullQueue, covariant=True)


class Projects(BaseTracker):
    """Legacy projects API (`/projects`).

    A project of this API is a set of queues with a lead, a status and a
    pair of dates. The projects shown in the current Tracker interface
    (with portfolios and goals) are entities: use the `Entities`
    category for them.
    """

    async def get_projects(
        self,
        *,
        expand: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> list[Project]:
        """Get projects.

        Use this request to get a list of all projects
        of the organization. Like every list request, the response is
        paginated by 50 objects; use `per_page` and `page` to fetch
        the rest.

        Source:
        https://yandex.ru/support/tracker/ru/api/projects/get-projects

        :param expand: additional fields to include into the response.
            The only documented value is `queues` — queues of the project.
        :param per_page: number of projects per page (50 by default).
        :param page: page number (1 by default).
        :return: list of projects.
        """
        params = {}
        if expand is not None:
            params["expand"] = expand
        if per_page is not None:
            params["perPage"] = str(per_page)
        if page is not None:
            params["page"] = str(page)

        data = await self._client.request(
            method="GET",
            uri="/projects",
            params=params or None,
        )
        return self._decode(list[Project], data)

    async def get_project(
        self,
        project_id: str | int,
        *,
        expand: str | None = None,
    ) -> Project:
        """Get project parameters.

        Source:
        https://yandex.ru/support/tracker/ru/api/projects/get-project

        :param project_id: ID of the project.
        :param expand: additional fields to include into the response.
            The only documented value is `queues` — queues of the project.
        :return: project.
        """
        params = {}
        if expand is not None:
            params["expand"] = expand

        data = await self._client.request(
            method="GET",
            uri=f"/projects/{project_id}",
            params=params or None,
        )
        return self._decode(Project, data)

    async def create_project(
        self,
        name: str,
        queues: str | Sequence[str],
        *,
        description: str | None = None,
        lead: str | int | None = None,
        status: str | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> Project:
        """Create a project.

        Source:
        https://yandex.ru/support/tracker/ru/api/projects/create-project

        :param name: project name.
        :param queues: keys of the queues of the project. The reference
            types this parameter as a single string, while the official
            `yandex_tracker_client` sends a list; whatever is passed is
            sent as is, so a string stays a string and a sequence becomes
            a JSON array.
        :param description: project description. It is not displayed in
            the Tracker interface.
        :param lead: ID or login of the project owner.
        :param status: project status: `DRAFT`, `IN_PROGRESS`,
            `LAUNCHED` or `POSTPONED`.
        :param start_date: project start date, a `date` or a `YYYY-MM-DD`
            string.
        :param end_date: project end date, a `date` or a `YYYY-MM-DD`
            string.
        :return: created project.
        """
        start_date = to_tracker_date(start_date)
        end_date = to_tracker_date(end_date)

        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/projects",
            payload=payload,
        )
        return self._decode(Project, data)

    async def update_project(
        self,
        project_id: str | int,
        version: str | int,
        queues: str | Sequence[str],
        *,
        name: str | None = None,
        description: str | None = None,
        lead: str | int | None = None,
        status: str | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        expand: str | None = None,
    ) -> Project:
        """Edit a project.

        Note that the API expects a `PUT` here and requires `queues` on
        every update: the queues of the project are replaced with the
        ones passed, so pass the current queues even when you only want
        to change, say, the status.

        Source:
        https://yandex.ru/support/tracker/ru/api/projects/update-project

        :param project_id: ID of the project to edit.
        :param version: current version of the project. The request
            fails with a 409 error (`AlreadyExistsError`) if the project
            was changed meanwhile.
        :param queues: keys of the queues of the project, a string or a
            sequence of strings (see `create_project`). Required.
        :param name: new project name.
        :param description: new project description.
        :param lead: ID or login of the new project owner.
        :param status: project status: `DRAFT`, `IN_PROGRESS`,
            `LAUNCHED` or `POSTPONED`.
        :param start_date: project start date, a `date` or a `YYYY-MM-DD`
            string.
        :param end_date: project end date, a `date` or a `YYYY-MM-DD`
            string.
        :param expand: additional fields to include into the response.
            The only documented value is `queues` — queues of the project.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated project.
        """
        start_date = to_tracker_date(start_date)
        end_date = to_tracker_date(end_date)

        payload = self._prepare_payload(
            locals(),
            exclude=["project_id", "version", "expand"],
        )

        params = {"version": str(version)}
        if expand is not None:
            params["expand"] = expand

        data = await self._client.request(
            method="PUT",
            uri=f"/projects/{project_id}",
            params=params,
            payload=payload,
        )
        return self._decode(Project, data)

    async def delete_project(self, project_id: str | int) -> bool:
        """Delete a project.

        The queues of the project are not deleted with it.

        Source:
        https://yandex.ru/support/tracker/ru/api/projects/delete-project

        :param project_id: ID of the project to delete.
        :return: `True` if the project was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/projects/{project_id}",
        )
        return True

    @overload
    async def get_project_queues(
        self,
        project_id: str | int,
        *,
        expand: str | None = ...,
        per_page: int | None = ...,
        page: int | None = ...,
    ) -> list[FullQueue]: ...

    @overload
    async def get_project_queues(
        self,
        project_id: str | int,
        _type: type[QueueT_co] = ...,
        *,
        expand: str | None = ...,
        per_page: int | None = ...,
        page: int | None = ...,
    ) -> list[QueueT_co]: ...

    async def get_project_queues(
        self,
        project_id: str | int,
        _type: type[QueueT_co | FullQueue] = FullQueue,
        *,
        expand: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> list[FullQueue] | list[QueueT_co]:
        """Get queues of a project.

        Like every list request, the response is paginated by 50
        objects; use `per_page` and `page` to fetch the rest.

        Source:
        https://yandex.ru/support/tracker/ru/api/projects/get-project-queues

        :param project_id: ID of the project.
        :param _type: you can use your own extended FullQueue type.
        :param expand: additional fields to include into the response.
            One of `all`, `projects`, `components`, `versions`, `types`,
            `team`, `workflows`, `fields`, `notification_fields`,
            `issue_types_config`, `enabled_feaures`,
            `signature_settings`. These are the values of the official
            get-project-queues page (the `enabled_feaures` typo
            included); `get_queue` documents the same field as
            `issueTypesConfig`, so if the snake_case form has no effect,
            try the camelCase one.
        :param per_page: number of queues per page (50 by default).
        :param page: page number (1 by default).
        :return: list of queues of the project.
        """
        params = {}
        if expand is not None:
            params["expand"] = expand
        if per_page is not None:
            params["perPage"] = str(per_page)
        if page is not None:
            params["page"] = str(page)

        data = await self._client.request(
            method="GET",
            uri=f"/projects/{project_id}/queues",
            params=params or None,
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]
