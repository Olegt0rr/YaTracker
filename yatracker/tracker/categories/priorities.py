from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
from yatracker.types.priority import Priority

if TYPE_CHECKING:
    from yatracker.types.localized_name import LocalizedName


class Priorities(BaseTracker):
    # ruff: noqa: FBT001 FBT002
    async def get_priorities(self, localized: bool = True) -> list[Priority]:
        """Get priorities.

        Use this request to get a list of priorities for an issue.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/get-priorities

        :param localized: `True` (the default) to get the priority names
            in the language of the user only, `False` to get them in
            every language: `name` then holds an object keyed by
            language instead of a string.
        :return: list of priorities.
        """
        params = {"localized": str(localized).lower()}
        data = await self._client.request(
            method="GET",
            uri="/priorities",
            params=params,
        )
        return self._decode(list[Priority], data)

    async def create_priority(
        self,
        key: str,
        name: LocalizedName | dict[str, str],
        order: int,
        description: str,
    ) -> Priority:
        """Create a priority.

        Admin rights are required. The API documents every parameter of
        this request as required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/create-priority

        :param key: key of the priority.
        :param name: name of the priority in every language, e.g.
            `LocalizedName(ru="Низкий", en="Low")` or
            `{"ru": "Низкий", "en": "Low"}`.
        :param order: weight of the priority; it affects the order the
            priorities are displayed in the interface.
        :param description: description of the priority.
        :return: created priority.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/priorities",
            payload=payload,
        )
        return self._decode(Priority, data)

    async def update_priority(
        self,
        priority_id: str | int,
        *,
        version: str | int | None = None,
        name: LocalizedName | dict[str, str] | None = None,
        description: str | None = None,
    ) -> Priority:
        """Edit a priority.

        Admin rights are required. The request cannot change the icon of
        the priority shown in the Tracker interface.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/patch-priority

        :param priority_id: ID or key of the priority to edit.
        :param version: current version of the priority, sent as the
            `version` query parameter: the changes are applied only to
            that version. The API answers 409 when the version is stale
            (:class:`AlreadyExistsError`) and 423 when the maximum
            version number is exceeded.
        :param name: new name of the priority in every language, e.g.
            `LocalizedName(ru="Низкий", en="Low")`.
        :param description: new description of the priority.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated priority.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["priority_id", "version"],
        )
        params = self._prepare_params(version=version)
        data = await self._client.request(
            method="PATCH",
            uri=f"/priorities/{priority_id}",
            params=params,
            payload=payload,
        )
        return self._decode(Priority, data)
