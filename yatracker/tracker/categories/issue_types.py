from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
from yatracker.types.issue_type import FullIssueType

if TYPE_CHECKING:
    from yatracker.types.localized_name import LocalizedNameInput


class IssueTypes(BaseTracker):
    async def get_issue_types(self) -> list[FullIssueType]:
        """Get issue types.

        Use this request to get a list of the available issue types.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/get-issue-types

        :return: list of issue types.
        """
        data = await self._client.request(
            method="GET",
            uri="/issuetypes",
        )
        return self._decode(list[FullIssueType], data)

    async def create_issue_type(
        self,
        key: str,
        name: LocalizedNameInput,
    ) -> FullIssueType:
        """Create an issue type.

        Admin rights are required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/create-issue-type

        :param key: key of the issue type.
        :param name: name of the issue type in every language, e.g.
            `LocalizedName(ru="Клиент", en="Customer")` or
            `{"ru": "Клиент", "en": "Customer"}`.
        :raises ValueError: if the API answered with an empty array.
        :return: created issue type.

        The reference shows the created issue type wrapped into a
        one-element array, while other single-object endpoints answer
        with a bare object; both shapes are accepted.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/issuetypes",
            payload=payload,
        )
        return self._decode_single(FullIssueType, data)

    async def update_issue_type(
        self,
        issue_type_id: str | int,
        *,
        version: str | int | None = None,
        name: LocalizedNameInput | None = None,
    ) -> FullIssueType:
        """Edit an issue type.

        Admin rights are required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/patch-issue-type

        :param issue_type_id: ID or key of the issue type to edit.
        :param version: current version of the issue type, sent as the
            `version` query parameter: the changes are applied only to
            that version. The API answers 409 when the version is stale
            (:class:`AlreadyExistsError`) and 423 when the maximum
            version number is exceeded.
        :param name: new name of the issue type in every language, e.g.
            `LocalizedName(ru="Покупатель", en="Customer")`.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        The reference shows the updated issue type wrapped into a
        one-element array, while other single-object endpoints answer
        with a bare object; both shapes are accepted.

        :raises ValueError: if the API answered with an empty array.
        :return: updated issue type.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["issue_type_id", "version"],
        )
        params = self._prepare_params(version=version)
        data = await self._client.request(
            method="PATCH",
            uri=f"/issuetypes/{issue_type_id}",
            params=params,
            payload=payload,
        )
        return self._decode_single(FullIssueType, data)
