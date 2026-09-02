from __future__ import annotations

__all__ = ["Project", "ProjectQueueRef"]

from datetime import date
from typing import Any, TypeVar, overload

from .base import Base, url_field
from .full_queue import FullQueue
from .user import User

QueueT_co = TypeVar("QueueT_co", bound=FullQueue, covariant=True)


class ProjectQueueRef(Base):
    """Queue reference embedded into a project for `expand="queues"`.

    The shape is not documented. Only `self` and `id` are required so that
    both a short reference (`self`, `id`, `key`, `display`) and a full
    queue object decode; use `get_project_queues` for full `FullQueue`
    objects.
    """

    url: str = url_field()
    id: str
    key: str | None = None
    display: str | None = None
    name: str | None = None


class Project(Base):
    """Legacy project (`/projects` API).

    This is the older projects API, where a project is a set of queues
    with a lead, a status and a pair of dates. The projects shown in the
    current Tracker interface (with portfolios and goals) are entities
    and live in the `/entities` API.

    Attributes
    ----------
    url - Reference to the object.
    id - Project ID.
    version - Project version. Each change of the project increments
    the version number.
    key - Project key. Matches the project name.
    name - Project name.
    description - Project description. It is not displayed in the
    Tracker interface.
    lead - Project owner.
    status - Project status: `draft`, `in_progress`, `launched` or
    `postponed` (the API answers in lower case, while requests take the
    upper case names).
    start_date - Project start date (`YYYY-MM-DD`).
    end_date - Project end date (`YYYY-MM-DD`).
    team_users - Project team members.
    team_groups - Project team groups. The shape of the objects is not
    documented, so they are kept as raw dicts.
    queues - Queues of the project, returned for `expand="queues"`.
    The exact shape is not documented, so they are decoded as tolerant
    `ProjectQueueRef` objects: both a short reference and a full queue
    object fit. Use `get_project_queues` for full `FullQueue` objects.

    Source:
    https://yandex.ru/support/tracker/ru/api/projects/get-project

    """

    url: str = url_field()
    id: str
    version: int
    key: str
    name: str
    description: str | None = None
    lead: User | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    # undocumented fields, declared by the official `yandex_tracker_client`
    team_users: list[User] | None = None
    team_groups: list[dict[str, Any]] | None = None
    queues: list[ProjectQueueRef] | None = None

    @overload
    async def get_queues(
        self,
        *,
        expand: str | None = ...,
        per_page: int | None = ...,
        page: int | None = ...,
    ) -> list[FullQueue]: ...

    @overload
    async def get_queues(
        self,
        _type: type[QueueT_co] = ...,
        *,
        expand: str | None = ...,
        per_page: int | None = ...,
        page: int | None = ...,
    ) -> list[QueueT_co]: ...

    async def get_queues(
        self,
        _type: type[QueueT_co | FullQueue] = FullQueue,
        *,
        expand: str | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> list[FullQueue] | list[QueueT_co]:
        """Get queues of self."""
        return await self._tracker.get_project_queues(
            self.id,
            _type,
            expand=expand,
            per_page=per_page,
            page=page,
        )

    async def delete(self) -> bool:
        """Delete self.

        :return: `True` if the project was deleted.
        """
        return await self._tracker.delete_project(self.id)
