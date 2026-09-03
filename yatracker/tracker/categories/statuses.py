from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
from yatracker.types.status import FullStatus

if TYPE_CHECKING:
    from yatracker.types.localized_name import LocalizedNameInput


class Statuses(BaseTracker):
    async def get_statuses(self) -> list[FullStatus]:
        """Get issue statuses.

        Use this request to get a list of the issue statuses.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/get-statuses

        :return: list of statuses.
        """
        data = await self._client.request(
            method="GET",
            uri="/statuses",
        )
        return self._decode(list[FullStatus], data)

    async def create_status(
        self,
        key: str,
        name: LocalizedNameInput,
        type_: str,
    ) -> FullStatus:
        """Create an issue status.

        Admin rights are required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/create-status

        :param key: key of the status. Latin letters only, must start
            with a lowercase one.
        :param name: name of the status in every language, e.g.
            `LocalizedName(ru="Мой статус", en="My status")` or
            `{"ru": "Мой статус", "en": "My status"}`.
        :param type_: type of the status: "new", "inProgress",
            "paused", "done" or "cancelled". Sent as `type`.
        :raises ValueError: if the API answered with an empty array.
        :return: created status.

        The reference shows the created status wrapped into a
        one-element array, while other single-object endpoints answer
        with a bare object; both shapes are accepted.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/statuses",
            payload=payload,
        )
        return self._decode_single(FullStatus, data)

    async def update_status(  # noqa: PLR0913
        self,
        status_id: str | int,
        *,
        version: str | int | None = None,
        name: LocalizedNameInput | None = None,
        description: str | None = None,
        order: int | None = None,
        type_: str | None = None,
    ) -> FullStatus:
        """Edit an issue status.

        Admin rights are required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/patch-status

        :param status_id: ID or key of the status to edit.
        :param version: current version of the status, sent as the
            `version` query parameter: the changes are applied only to
            that version. The API answers 412 when the version is stale
            (:class:`PreconditionFailedError`) and 423 when the maximum
            version number is exceeded.
        :param name: new name of the status in every language, e.g.
            `LocalizedName(ru="Приостановлен", en="On pause")`.
        :param description: new description of the status.
        :param order: new weight of the status; it affects the order the
            statuses are displayed in the interface.
        :param type_: new type of the status: "new", "inProgress",
            "paused", "done" or "cancelled". Sent as `type`.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        The reference shows the updated status wrapped into a
        one-element array, while other single-object endpoints answer
        with a bare object; both shapes are accepted.

        :raises ValueError: if the API answered with an empty array.
        :return: updated status.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["status_id", "version"],
        )
        params = self._prepare_params(version=version)
        data = await self._client.request(
            method="PATCH",
            uri=f"/statuses/{status_id}",
            params=params,
            payload=payload,
        )
        return self._decode_single(FullStatus, data)
