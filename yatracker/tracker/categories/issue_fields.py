from __future__ import annotations

from typing import Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.field_category import FieldCategory
from yatracker.types.issue_field import IssueField
from yatracker.types.local_field import LocalField
from yatracker.types.localized_name import LocalizedNameInput
from yatracker.types.queue_field_options_provider import QueueFieldOptionsProvider

OptionsProviderT = QueueFieldOptionsProvider | dict[str, Any]


class IssueFields(BaseTracker):
    """Global issue fields, local queue fields and field categories.

    Global fields (`/fields`) can be used in the issues of every queue
    of the organization, local fields (`/queues/{id}/localFields`) only
    in the issues of the queue they are bound to. The id of a local
    field carries a hexadecimal prefix and the field key
    (`603fb94c38bbe658********--myfield`) and has to be used verbatim
    when the field value of an issue is read or written.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/fields
    """

    async def get_global_fields(self) -> list[IssueField]:
        """Get all global fields of the organization.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-global-fields

        :return: list of global fields.
        """
        data = await self._client.request(
            method="GET",
            uri="/fields",
        )
        return self._decode(list[IssueField], data)

    async def get_field(self, field_id: str | int) -> IssueField:
        """Get the parameters of an issue field.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-issue-fields

        :param field_id: ID of the field.
        :return: the field.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/fields/{field_id}",
        )
        return self._decode(IssueField, data)

    async def create_field(  # noqa: PLR0913
        self,
        name: LocalizedNameInput,
        id_: str,
        category: str,
        type_: str,
        *,
        options_provider: OptionsProviderT | None = None,
        order: int | None = None,
        description: str | None = None,
        readonly: bool | None = None,
        visible: bool | None = None,
        hidden: bool | None = None,
        container: bool | None = None,
    ) -> IssueField:
        """Create a global issue field.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/create-field

        :param name: localized field name, e.g.
            `LocalizedName(en="Name", ru="Название")`.
        :param id_: ID of the new field, sent as `id` (the trailing
            underscore keeps the name out of the way of the builtin,
            like `type_`).
        :param category: ID of the field category. The list of
            categories is served by `GET /fields/categories`.
        :param type_: field type, one of
            `ru.yandex.startrek.core.fields.DateFieldType`,
            `...DateTimeFieldType`, `...StringFieldType`,
            `...TextFieldType`, `...FloatFieldType`,
            `...IntegerFieldType`, `...UserFieldType`,
            `...UriFieldType`, `...MoneyFieldType`,
            `...MoneyWithRateFieldType`,
            `...TimeTrackingDurationFieldType`.
        :param options_provider: drop-down list of the field, e.g.
            `{"type": "FixedListOptionsProvider", "values": [...]}`.
            `type` is `FixedListOptionsProvider` for string or integer
            fields and `FixedUserListOptionsProvider` for user fields.
        :param order: position of the field in the organization field list.
        :param description: field description.
        :param readonly: `True` if the value cannot be changed.
        :param visible: `True` to always show the field in the interface.
        :param hidden: `True` to hide the field even when it is filled in.
        :param container: `True` if several values can be set at once
            (allowed for string fields, user fields and drop-down lists).

        Fields left as ``None`` are not sent.

        :return: created field.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/fields",
            payload=payload,
        )
        return self._decode(IssueField, data)

    async def update_field(  # noqa: PLR0913
        self,
        field_id: str | int,
        version: str | int,
        *,
        name: LocalizedNameInput | None = None,
        category: str | None = None,
        order: int | None = None,
        description: str | None = None,
        readonly: bool | None = None,
        visible: bool | None = None,
        hidden: bool | None = None,
        options_provider: OptionsProviderT | None = None,
    ) -> IssueField:
        """Edit a global issue field.

        One endpoint covers both documented use cases: renaming the
        field and changing the values it allows.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-name
        https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-value

        :param field_id: ID of the field to edit.
        :param version: current version of the field, sent as the
            `version` query parameter. The request fails with 412 if the
            field was changed meanwhile.
        :param name: new localized field name.
        :param category: ID of the new field category.
        :param order: new position in the organization field list.
        :param description: new field description.
        :param readonly: `True` if the value cannot be changed.
        :param visible: `True` to always show the field in the interface.
        :param hidden: `True` to hide the field even when it is filled in.
        :param options_provider: new allowed values of the field, e.g.
            `{"type": "FixedListOptionsProvider", "values": [...]}`.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated field.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["field_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/fields/{field_id}",
            params=self._prepare_params(version=version),
            payload=payload,
        )
        return self._decode(IssueField, data)

    async def create_field_category(
        self,
        name: LocalizedNameInput,
        order: int,
        *,
        description: str | None = None,
    ) -> FieldCategory:
        """Create a category of issue fields.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/create-issue-field-category

        :param name: localized category name, e.g.
            `LocalizedName(en="Name", ru="Название")`.
        :param order: weight of the category in the interface; lighter
            categories are shown above heavier ones.
        :param description: category description.
        :return: created category.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/fields/categories",
            payload=payload,
        )
        return self._decode(FieldCategory, data)

    async def update_field_category(
        self,
        category_id: str | int,
        *,
        version: str | int | None = None,
        name: LocalizedNameInput | None = None,
        order: int | None = None,
        description: str | None = None,
    ) -> FieldCategory:
        """Edit a category of issue fields.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-category

        :param category_id: ID of the category to edit.
        :param version: current version of the category, sent as the
            `version` query parameter. Only the current version of the
            category is changed.
        :param name: new localized category name.
        :param order: new weight of the category in the interface.
        :param description: new category description.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated category.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["category_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/fields/categories/{category_id}",
            params=self._prepare_params(version=version),
            payload=payload,
        )
        return self._decode(FieldCategory, data)

    async def get_local_fields(self, queue_id: str | int) -> list[LocalField]:
        """Get the local fields of a queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-local-fields

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :return: list of local fields of the queue.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/localFields",
        )
        return self._decode(list[LocalField], data)

    async def get_local_field(
        self,
        queue_id: str | int,
        field_key: str,
    ) -> LocalField:
        """Get a local field of a queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-info-local-field

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :param field_key: key of the local field (the `key` of the
            objects returned by :meth:`get_local_fields`, not the
            prefixed `<hex>--key` id).
        :return: the local field.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/localFields/{field_key}",
        )
        return self._decode(LocalField, data)

    async def create_local_field(  # noqa: PLR0913
        self,
        queue_id: str | int,
        name: LocalizedNameInput,
        id_: str,
        category: str,
        type_: str,
        *,
        options_provider: OptionsProviderT | None = None,
        order: int | None = None,
        description: str | None = None,
        readonly: bool | None = None,
        visible: bool | None = None,
        hidden: bool | None = None,
        container: bool | None = None,
    ) -> LocalField:
        """Create a local field bound to a queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/create-local-field

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :param name: localized field name, e.g.
            `LocalizedName(en="Name", ru="Название")`.
        :param id_: key of the new local field, sent as `id` (the
            trailing underscore keeps the name out of the way of the
            builtin, like `type_`). The created field gets the prefixed
            id `<hex>--<id_>`.
        :param category: ID of the field category. The list of
            categories is served by `GET /fields/categories`.
        :param type_: field type, one of
            `ru.yandex.startrek.core.fields.DateFieldType`,
            `...DateTimeFieldType`, `...StringFieldType`,
            `...TextFieldType`, `...FloatFieldType`,
            `...IntegerFieldType`, `...UserFieldType`,
            `...UriFieldType`, `...MoneyFieldType`,
            `...MoneyWithRateFieldType`,
            `...TimeTrackingDurationFieldType`.
        :param options_provider: drop-down list of the field, e.g.
            `{"type": "FixedListOptionsProvider", "values": [...]}`.
            `type` is `FixedListOptionsProvider` for string or integer
            fields and `FixedUserListOptionsProvider` for user fields.
        :param order: position of the field in the organization field list.
        :param description: field description.
        :param readonly: `True` if the value cannot be changed.
        :param visible: `True` to always show the field in the interface.
        :param hidden: `True` to hide the field even when it is filled in.
        :param container: `True` if several values can be set at once
            (allowed for string fields, user fields and drop-down lists).

        Fields left as ``None`` are not sent.

        :return: created local field.
        """
        payload = self._prepare_payload(locals(), exclude=["queue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/queues/{queue_id}/localFields",
            payload=payload,
        )
        return self._decode(LocalField, data)

    async def update_local_field(  # noqa: PLR0913
        self,
        queue_id: str | int,
        field_key: str,
        *,
        name: LocalizedNameInput | None = None,
        category: str | None = None,
        order: int | None = None,
        description: str | None = None,
        options_provider: OptionsProviderT | None = None,
        readonly: bool | None = None,
        visible: bool | None = None,
        hidden: bool | None = None,
    ) -> LocalField:
        """Edit a local field of a queue.

        Unlike the global-field endpoint, this one takes no `version`.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/edit-local-field

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :param field_key: key of the local field (the `key` of the
            objects returned by :meth:`get_local_fields`, not the
            prefixed `<hex>--key` id).
        :param name: new localized field name.
        :param category: ID of the new field category.
        :param order: new position in the organization field list.
        :param description: new field description.
        :param options_provider: new drop-down list of the field, e.g.
            `{"type": "FixedListOptionsProvider", "values": [...]}`.
        :param readonly: `True` if the value cannot be changed.
        :param visible: `True` to always show the field in issues, even
            when it is empty.
        :param hidden: `True` to hide the field completely, even when it
            is filled in.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated local field.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["queue_id", "field_key"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/queues/{queue_id}/localFields/{field_key}",
            payload=payload,
        )
        return self._decode(LocalField, data)
