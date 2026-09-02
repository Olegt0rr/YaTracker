from __future__ import annotations

__all__ = [
    "Board",
    "BoardCalendar",
    "BoardColumn",
    "BoardColumnParams",
    "BoardColumnRef",
    "BoardRef",
    "CountryRef",
    "FieldRef",
]

from datetime import datetime
from typing import TYPE_CHECKING, Any

from .base import Base, field
from .status import Status
from .user import User

if TYPE_CHECKING:
    from .sprint import FullSprint


class BoardRef(Base):
    """Short board reference embedded into a sprint object.

    Sprint payloads carry only `self`, `id` and `display` for the board
    the sprint belongs to.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprint
    """

    url: str = field(alias="self")
    id: str
    display: str | None = None


class BoardColumnRef(Base):
    """Short column reference embedded into a board object.

    A board payload carries only `self`, `id` and `display` for every
    column; use `get_board_columns` for the full objects.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board
    """

    url: str = field(alias="self")
    id: str
    display: str | None = None


class FieldRef(Base):
    """Short field reference used by the deprecated `estimateBy` field.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board
    """

    url: str = field(alias="self")
    id: str
    display: str | None = None


class CountryRef(Base):
    """Short country reference used by the deprecated `country` field.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board
    """

    url: str = field(alias="self")
    id: str
    display: str | None = None


class BoardCalendar(Base):
    """Production calendar of the board."""

    id: str


class Board(Base):
    """Agile board.

    `use_ranking`, `estimate_by` and `country` are documented as
    deprecated: the API still returns them, but they no longer affect
    anything. The inner shape of `auto_filter_settings` is not
    documented, so it is kept as a plain dict.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board
    """

    url: str = field(alias="self")
    id: str
    version: int
    name: str
    created_at: datetime
    created_by: User
    updated_at: datetime | None = None
    columns: list[BoardColumnRef] | None = None
    # the three fields below are deprecated by the API, see the docstring
    use_ranking: bool | None = None
    estimate_by: FieldRef | None = None
    country: CountryRef | None = None
    calendar: BoardCalendar | None = None
    auto_filter_settings: dict[str, Any] | None = None

    async def get_columns(self) -> list[BoardColumn]:
        """Get the columns of this board."""
        return await self._tracker.get_board_columns(self.id)

    async def get_sprints(self) -> list[FullSprint]:
        """Get the sprints of this board."""
        return await self._tracker.get_sprints(self.id)


class BoardColumn(Base):
    """Column of an agile board.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-column
    """

    url: str = field(alias="self")
    id: str
    name: str
    statuses: list[Status] | None = None


class BoardColumnParams(Base):
    """Column description for `create_board` / `update_board`.

    This is a request-side only object: the API answers with
    :class:`BoardColumn` objects, which carry full statuses instead of
    their keys.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/post-board
    """

    name: str
    # status keys; omit for backlog and non-parametrized columns
    statuses: list[str] | None = None
    limit: int | None = None
