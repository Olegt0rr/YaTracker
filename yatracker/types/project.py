from __future__ import annotations

__all__ = ["Project"]

from datetime import date
from typing import Any

from .base import Base, field
from .full_queue import FullQueue
from .user import User


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
    The exact shape is not documented; it is assumed to be the same as
    of `GET /projects/{id}/queues` by analogy with `get_project_queues`.

    Source:
    https://yandex.ru/support/tracker/ru/api/projects/get-project

    """

    url: str = field(alias="self")
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
    queues: list[FullQueue] | None = None

    async def get_queues(self, *, expand: str | None = None) -> list[FullQueue]:
        """Get queues of self."""
        return await self._tracker.get_project_queues(self.id, expand=expand)

    async def delete(self) -> None:
        """Delete self."""
        return await self._tracker.delete_project(self.id)
