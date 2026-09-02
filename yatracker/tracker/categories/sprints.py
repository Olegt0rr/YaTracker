from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker, _if_match
from yatracker.types import FullSprint
from yatracker.utils.datetime import to_tracker_date

if TYPE_CHECKING:
    from datetime import date


class Sprints(BaseTracker):
    async def get_sprints(self, board_id: str | int) -> list[FullSprint]:
        """Get the sprints of a board.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprints

        :param board_id: ID of the board.
        :return: list of sprints.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/boards/{board_id}/sprints",
        )
        return self._decode(list[FullSprint], data)

    async def get_sprint(self, sprint_id: str | int) -> FullSprint:
        """Get a sprint.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprint

        :param sprint_id: ID of the sprint.
        :return: sprint.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/sprints/{sprint_id}",
        )
        return self._decode(FullSprint, data)

    async def create_sprint(
        self,
        name: str,
        board_id: str | int,
        start_date: date | str,
        end_date: date | str,
    ) -> FullSprint:
        """Create a sprint.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/post-sprint

        :param name: sprint name.
        :param board_id: ID of the board the sprint belongs to.
        :param start_date: start date, `YYYY-MM-DD` or a `date` object.
        :param end_date: end date, `YYYY-MM-DD` or a `date` object.
        :return: created sprint.
        """
        start_date = to_tracker_date(start_date)
        end_date = to_tracker_date(end_date)

        payload = self._prepare_payload(locals(), exclude=["board_id"])
        payload["board"] = {"id": str(board_id)}
        data = await self._client.request(
            method="POST",
            uri="/sprints",
            payload=payload,
        )
        return self._decode(FullSprint, data)

    async def update_sprint(  # noqa: PLR0913
        self,
        sprint_id: str | int,
        version: str | int,
        *,
        name: str | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        status: str | None = None,
    ) -> FullSprint:
        """Edit a sprint.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-sprint

        :param sprint_id: ID of the sprint to edit.
        :param version: current version of the sprint, sent in the
            `If-Match` header. The request fails with
            :class:`PreconditionFailedError` (412) if the sprint was
            changed meanwhile.
        :param name: new sprint name.
        :param start_date: new start date, `YYYY-MM-DD` or a `date`.
        :param end_date: new end date, `YYYY-MM-DD` or a `date`.
        :param status: new sprint status: "draft", "in_progress",
            "released" or "archived".

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated sprint.
        """
        start_date = to_tracker_date(start_date)
        end_date = to_tracker_date(end_date)

        payload = self._prepare_payload(
            locals(),
            exclude=["sprint_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/sprints/{sprint_id}",
            payload=payload,
            headers=_if_match(version),
        )
        return self._decode(FullSprint, data)

    async def start_sprint(
        self,
        sprint_id: str | int,
        version: str | int,
    ) -> FullSprint:
        """Start a sprint.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/start-sprint

        :param sprint_id: ID of the sprint to start.
        :param version: current version of the sprint, sent in the
            `If-Match` header. The request fails with
            :class:`PreconditionFailedError` (412) if the sprint was
            changed meanwhile.
        :return: started sprint.
        """
        data = await self._client.request(
            method="POST",
            uri=f"/sprints/{sprint_id}/_start",
            # the docs list `Content-Type: application/json` for this
            # request, so an empty JSON object is sent instead of no body
            payload={},
            headers=_if_match(version),
        )
        return self._decode(FullSprint, data)

    async def archive_sprint(
        self,
        sprint_id: str | int,
        version: str | int,
    ) -> FullSprint:
        """Archive a sprint.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/archive-sprint

        :param sprint_id: ID of the sprint to archive.
        :param version: current version of the sprint, sent in the
            `If-Match` header. The request fails with
            :class:`PreconditionFailedError` (412) if the sprint was
            changed meanwhile.
        :return: archived sprint.
        """
        data = await self._client.request(
            method="POST",
            uri=f"/sprints/{sprint_id}/_archive",
            # the docs list `Content-Type: application/json` for this
            # request, so an empty JSON object is sent instead of no body
            payload={},
            headers=_if_match(version),
        )
        return self._decode(FullSprint, data)

    async def delete_sprint(self, sprint_id: str | int) -> bool:
        """Delete a sprint.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-sprint

        :param sprint_id: ID of the sprint to delete.
        :return: True on success.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/sprints/{sprint_id}",
        )
        return True
