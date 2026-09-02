from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import (
    BaseTracker,
    _if_match,
    _iter_relative,
    _relative_page_size,
)
from yatracker.types import Board, BoardColumn

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from yatracker.types import BoardColumnParams


class Boards(BaseTracker):
    async def get_boards(self) -> list[Board]:
        """Get boards.

        Use this request to get a list of all boards available to the
        user. The response is not paginated; use
        :meth:`get_boards_paginated` or :meth:`iter_boards` when the
        organization has a lot of boards.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards

        :return: list of boards.
        """
        data = await self._client.request(
            method="GET",
            uri="/boards",
        )
        return self._decode(list[Board], data)

    async def get_boards_paginated(
        self,
        per_page: int | None = None,
        id_: str | int | None = None,
    ) -> list[Board]:
        """Get one page of boards (relative pagination).

        Boards are sorted by id in ascending order, so the next page is
        requested with the id of the last board of the current one.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards-paginate

        :param per_page: number of boards per page (500 at most).
        :param id_: id of the last board of the previous page
            (query param "id"). Omit it to get the first page.
        :return: list of boards.
        """
        params: dict[str, str] = {}
        if per_page is not None:
            params["perPage"] = str(per_page)
        if id_ is not None:
            params["id"] = str(id_)

        data = await self._client.request(
            method="GET",
            uri="/boards/_paginate",
            params=params or None,
        )
        return self._decode(list[Board], data)

    async def iter_boards(
        self,
        per_page: int | None = None,
    ) -> AsyncIterator[Board]:
        """Iterate over all boards, page by page.

        Wraps :meth:`get_boards_paginated`: every page is requested with
        the id of the last board of the previous one (see
        :func:`yatracker.tracker.base._iter_relative`).

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards-paginate

        :param per_page: number of boards per page (500 at most).
            `per_page=1` is sent as 2: the cursor board is resent on
            every page, so a page of one could never advance.
        """
        page_size = _relative_page_size(per_page)

        async def fetch_page(id_: str | None) -> list[Board]:
            return await self.get_boards_paginated(per_page=page_size, id_=id_)

        async for board in _iter_relative(
            fetch_page,
            items=lambda page: page,
            key=lambda board: board.id,
        ):
            yield board

    async def get_board(self, board_id: str | int) -> Board:
        """Get a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board

        :param board_id: ID of the board.
        :return: board.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/boards/{board_id}",
        )
        return self._decode(Board, data)

    async def create_board(  # noqa: PLR0913
        self,
        name: str,
        *,
        owner: str | int | None = None,
        board_permissions_template: str | None = None,
        backlog_available: bool | None = None,
        sprints_available: bool | None = None,
        columns: list[BoardColumnParams] | None = None,
        backlog_columns: list[BoardColumnParams] | None = None,
        non_parametrized_columns: list[BoardColumnParams] | None = None,
        auto_filters: dict[str, Any] | None = None,
    ) -> Board:
        """Create a board.

        The board is created via `POST /liveBoards/`: the older
        `POST /boards/` endpoint is deprecated and silently ignores the
        request body.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/post-board

        :param name: board name.
        :param owner: login or uid of the board owner (the calling user
            by default).
        :param board_permissions_template: "private" (only the owner may
            edit the board) or "public" (default).
        :param backlog_available: whether the board has a backlog.
        :param sprints_available: whether the board has sprints.
        :param columns: columns of the board.
        :param backlog_columns: columns of the backlog.
        :param non_parametrized_columns: columns not bound to statuses.
        :param auto_filters: auto filter settings, sent verbatim; see
            the `autoFilters` object of the API reference.
        :return: created board.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/liveBoards/",
            payload=payload,
        )
        return self._decode(Board, data)

    async def update_board(  # noqa: PLR0913
        self,
        board_id: str | int,
        *,
        version: str | int | None = None,
        name: str | None = None,
        backlog_available: bool | None = None,
        sprints_available: bool | None = None,
        columns: list[BoardColumnParams] | None = None,
        backlog_columns: list[BoardColumnParams] | None = None,
        non_parametrized_columns: list[BoardColumnParams] | None = None,
    ) -> Board:
        """Edit a board.

        The owner of a board cannot be changed.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-board

        :param board_id: ID of the board to edit.
        :param version: current version of the board. When given, it is
            sent in the `If-Match` header. The API reference does not
            list that header for this endpoint, but it does document the
            412 (:class:`PreconditionFailedError`, stale version) and 428
            (:class:`PreconditionRequiredError`, version required)
            responses, so the header is passed through as is. Without
            `version` the request carries no lost-update guard.
        :param name: new board name.
        :param backlog_available: whether the board has a backlog.
        :param sprints_available: whether the board has sprints.
        :param columns: new columns of the board.
        :param backlog_columns: new columns of the backlog.
        :param non_parametrized_columns: new columns not bound to statuses.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated board.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["board_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/boards/{board_id}",
            payload=payload,
            headers=_if_match(version) if version is not None else None,
        )
        return self._decode(Board, data)

    async def delete_board(self, board_id: str | int) -> bool:
        """Delete a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-board

        :param board_id: ID of the board to delete.
        :return: True on success.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/boards/{board_id}",
        )
        return True

    async def get_board_columns(self, board_id: str | int) -> list[BoardColumn]:
        """Get the columns of a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-columns

        :param board_id: ID of the board.
        :return: list of columns.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/boards/{board_id}/columns",
        )
        return self._decode(list[BoardColumn], data)

    async def get_board_column(
        self,
        board_id: str | int,
        column_id: str | int,
    ) -> BoardColumn:
        """Get a column of a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-column

        :param board_id: ID of the board.
        :param column_id: ID of the column.
        :return: column.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/boards/{board_id}/columns/{column_id}",
        )
        return self._decode(BoardColumn, data)

    async def create_board_column(
        self,
        board_id: str | int,
        version: str | int,
        name: str,
        statuses: list[str],
    ) -> BoardColumn:
        """Create a column of a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/post-column

        :param board_id: ID of the board.
        :param version: current version of the **board** (not of the
            column), sent in the `If-Match` header. The request fails
            with :class:`PreconditionFailedError` (412) if the board was
            changed meanwhile.
        :param name: column name.
        :param statuses: keys of the statuses the column consists of.
        :return: created column.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["board_id", "version"],
        )
        data = await self._client.request(
            method="POST",
            uri=f"/boards/{board_id}/columns/",
            payload=payload,
            headers=_if_match(version),
        )
        return self._decode(BoardColumn, data)

    async def update_board_column(
        self,
        board_id: str | int,
        column_id: str | int,
        version: str | int,
        *,
        name: str | None = None,
        statuses: list[str] | None = None,
    ) -> BoardColumn:
        """Edit a column of a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-column

        :param board_id: ID of the board.
        :param column_id: ID of the column to edit.
        :param version: current version of the **board** (not of the
            column), sent in the `If-Match` header. The request fails
            with :class:`PreconditionFailedError` (412) if the board was
            changed meanwhile.
        :param name: new column name.
        :param statuses: keys of the statuses the column consists of.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated column.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["board_id", "column_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/boards/{board_id}/columns/{column_id}",
            payload=payload,
            headers=_if_match(version),
        )
        return self._decode(BoardColumn, data)

    async def delete_board_column(
        self,
        board_id: str | int,
        column_id: str | int,
        version: str | int,
    ) -> bool:
        """Delete a column of a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-column

        :param board_id: ID of the board.
        :param column_id: ID of the column to delete.
        :param version: current version of the **board** (not of the
            column), sent in the `If-Match` header. The request fails
            with :class:`PreconditionFailedError` (412) if the board was
            changed meanwhile.
        :return: True on success.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/boards/{board_id}/columns/{column_id}",
            headers=_if_match(version),
        )
        return True
