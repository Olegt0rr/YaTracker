from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker, _check_sequence, _convert_value
from yatracker.types.entity import (
    ChecklistEntityType,
    Entity,
    EntityChecklistItem,
    EntityDeadline,
)
from yatracker.utils.datetime import to_tracker_datetime

from .entities import _entity_uri, _fields_params

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import date, datetime


class EntityChecklists(BaseTracker):
    """Checklists of projects and portfolios (`/entities`).

    The whole checklist is also reachable through the entity itself:
    `get_entity(..., fields="checklistItems")` reads it and
    `update_entity(..., checklist_items=[...])` rewrites it.

    Every method here answers with the whole entity, not with the
    checklist, so ask for the items with `fields="checklistItems"`.

    Only projects and portfolios have a checklist, so every method here
    takes a `ChecklistEntityType` ("project" or "portfolio") rather than
    the wider `EntityType` of the other entity categories.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/checklists/add-checklist
    """

    async def add_entity_checklist_item(  # noqa: PLR0913
        self,
        entity_type: ChecklistEntityType,
        entity_id: str | int,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: EntityDeadline | datetime | date | str | None = None,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Add an item to the checklist of an entity.

        The item is appended to the end of the list; the checklist is
        created if the entity does not have one yet.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/checklists/add-checklist

        :param entity_type: "project" or "portfolio" (the checklist
            endpoints are not documented for goals).
        :param entity_id: Id (or short id) of the entity.
        :param text: Text of the checklist item.
        :param checked: Mark the item as done.
        :param assignee: Login or id of the assignee of the item.
        :param deadline: Deadline of the item: an `EntityDeadline`, a
            timezone-aware `datetime` or a `date` (both sent as type
            `date`), or a ready-made API string. The API documents the
            date as a full timestamp, so a bare `date` is sent as
            midnight UTC; pass an aware `datetime` when the offset
            matters.
        :param notify: Whether to notify the users mentioned in the
            entity (`True` by default).
        :param notify_author: Whether to notify the author of the
            change (`False` by default).
        :param fields: Fields to return in the response (a
            comma-separated string or a sequence of names).
        :param expand: Additional information to include,
            e.g. "attachments".
        :return: The whole entity, not the created item.
        """
        payload = _checklist_item_payload(
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=deadline,
        )

        data = await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type, str(entity_id), "checklistItems"),
            params=_fields_params(
                fields,
                expand=expand,
                notify=notify,
                notify_author=notify_author,
            ),
            payload=payload,
        )
        return self._decode(Entity, data)

    async def edit_entity_checklist(  # noqa: PLR0913
        self,
        entity_type: ChecklistEntityType,
        entity_id: str | int,
        items: Sequence[EntityChecklistItem | dict[str, Any]],
        *,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Edit several items of the checklist of an entity at once.

        Every item is identified by its `id` and needs its `text`; the
        optional fields that are not repeated are reset to their default
        value (an empty string, `0`, `null` or `false`), so pass back
        the values that should stay as they are. The number of items
        cannot change here: use `add_entity_checklist_item` and
        `delete_entity_checklist_item` for that.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist

        :param entity_type: "project" or "portfolio" (the checklist
            endpoints are not documented for goals).
        :param entity_id: Id (or short id) of the entity.
        :param items: Items to edit: `EntityChecklistItem` objects or
            dicts like `{"id": "...", "text": "...", "checked": True}`.
            An `EntityChecklistItem` (e.g. one read back from the API)
            is re-encoded into the request shape: its assignee is sent
            as a user id and the read-only `text_html`,
            `checklist_item_type` and `deadline.is_exceeded` are
            dropped. A dict is sent as it is.
            A single item on its own raises `TypeError`.
        :param notify: Whether to notify the users mentioned in the
            entity (`True` by default).
        :param notify_author: Whether to notify the author of the
            change (`False` by default).
        :param fields: Fields to return in the response.
        :param expand: Additional information to include,
            e.g. "attachments".
        :raises TypeError: If `items` is a bare item instead of a
            sequence.
        :raises ValueError: If there are no items to edit.
        :return: The whole entity, not the edited items.
        """
        payload = _checklist_items_payload(items)

        data = await self._client.request(
            method="PATCH",
            uri=_entity_uri(entity_type, str(entity_id), "checklistItems"),
            params=_fields_params(
                fields,
                expand=expand,
                notify=notify,
                notify_author=notify_author,
            ),
            payload=payload,
        )
        return self._decode(Entity, data)

    async def edit_entity_checklist_item(  # noqa: PLR0913
        self,
        entity_type: ChecklistEntityType,
        entity_id: str | int,
        item_id: str,
        *,
        text: str | None = None,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: EntityDeadline | datetime | date | str | None = None,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Edit a single item of the checklist of an entity.

        Fields left as `None` are not sent. The documentation does not
        say how the fields that are not sent are treated, so do not rely
        on them keeping their current values.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist-item

        :param entity_type: "project" or "portfolio" (the checklist
            endpoints are not documented for goals).
        :param entity_id: Id (or short id) of the entity.
        :param item_id: Id of the checklist item to edit.
        :param text: Text of the checklist item.
        :param checked: Mark the item as done.
        :param assignee: Login or id of the assignee of the item.
        :param deadline: Deadline of the item: an `EntityDeadline`, a
            timezone-aware `datetime` or a `date` (both sent as type
            `date`), or a ready-made API string. The API documents the
            date as a full timestamp, so a bare `date` is sent as
            midnight UTC; pass an aware `datetime` when the offset
            matters.
        :param notify: Whether to notify the users mentioned in the
            entity (`True` by default).
        :param notify_author: Whether to notify the author of the
            change (`False` by default).
        :param fields: Fields to return in the response.
        :param expand: Additional information to include,
            e.g. "attachments".
        :raises ValueError: If there is nothing to change.
        :return: The whole entity, not the edited item.
        """
        payload = _checklist_item_payload(
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=deadline,
        )
        if not payload:
            msg = "This operation requires at least one field to change."
            raise ValueError(msg)

        data = await self._client.request(
            method="PATCH",
            uri=_entity_uri(
                entity_type,
                str(entity_id),
                "checklistItems",
                str(item_id),
            ),
            params=_fields_params(
                fields,
                expand=expand,
                notify=notify,
                notify_author=notify_author,
            ),
            payload=payload,
        )
        return self._decode(Entity, data)

    async def move_entity_checklist_item(  # noqa: PLR0913
        self,
        entity_type: ChecklistEntityType,
        entity_id: str | int,
        item_id: str,
        before: str,
        *,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Move an item of the checklist of an entity.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/checklists/move-checklist-item

        :param entity_type: "project" or "portfolio" (the checklist
            endpoints are not documented for goals).
        :param entity_id: Id (or short id) of the entity.
        :param item_id: Id of the checklist item to move.
        :param before: Id of the checklist item to insert the moved item
            before.
        :param notify: Whether to notify the users mentioned in the
            entity (`True` by default).
        :param notify_author: Whether to notify the author of the
            change (`False` by default).
        :param fields: Fields to return in the response.
        :param expand: Additional information to include,
            e.g. "attachments".
        :return: The whole entity, not the moved item.
        """
        data = await self._client.request(
            method="POST",
            uri=_entity_uri(
                entity_type,
                str(entity_id),
                "checklistItems",
                str(item_id),
                "_move",
            ),
            params=_fields_params(
                fields,
                expand=expand,
                notify=notify,
                notify_author=notify_author,
            ),
            payload={"before": before},
        )
        return self._decode(Entity, data)

    async def delete_entity_checklist_item(  # noqa: PLR0913
        self,
        entity_type: ChecklistEntityType,
        entity_id: str | int,
        item_id: str,
        *,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Delete an item from the checklist of an entity.

        The action cannot be undone. Unlike the issue-side
        `delete_checklist_item`, which is a plain `DELETE`, this
        endpoint answers 200 with the whole entity and its remaining
        checklist items, so ask for them with `fields="checklistItems"`
        instead of re-reading the entity.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/checklists/delete-checklist-item

        :param entity_type: "project" or "portfolio" (the checklist
            endpoints are not documented for goals).
        :param entity_id: Id (or short id) of the entity.
        :param item_id: Id of the checklist item to delete.
        :param notify: Whether to notify the users mentioned in the
            entity (`True` by default).
        :param notify_author: Whether to notify the author of the
            change (`False` by default).
        :param fields: Fields to return in the response (a
            comma-separated string or a sequence of names).
        :param expand: Additional information to include,
            e.g. "attachments".
        :return: The whole entity, with the checklist items that are
            left when `fields="checklistItems"` is asked for.
        """
        data = await self._client.request(
            method="DELETE",
            uri=_entity_uri(
                entity_type,
                str(entity_id),
                "checklistItems",
                str(item_id),
            ),
            params=_fields_params(
                fields,
                expand=expand,
                notify=notify,
                notify_author=notify_author,
            ),
        )
        return self._decode(Entity, data)

    async def delete_entity_checklist(  # noqa: PLR0913
        self,
        entity_type: ChecklistEntityType,
        entity_id: str | int,
        *,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Delete every item of the checklist of an entity.

        The action cannot be undone. Unlike the issue-side
        `delete_checklist`, which is a plain `DELETE`, this endpoint
        answers 200 with the whole entity the checklist was removed
        from.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/checklists/delete-checklist

        :param entity_type: "project" or "portfolio" (the checklist
            endpoints are not documented for goals).
        :param entity_id: Id (or short id) of the entity.
        :param notify: Whether to notify the users mentioned in the
            entity (`True` by default).
        :param notify_author: Whether to notify the author of the
            change (`False` by default).
        :param fields: Fields to return in the response (a
            comma-separated string or a sequence of names).
        :param expand: Additional information to include,
            e.g. "attachments".
        :return: The whole entity the checklist was deleted from.
        """
        data = await self._client.request(
            method="DELETE",
            uri=_entity_uri(entity_type, str(entity_id), "checklistItems"),
            params=_fields_params(
                fields,
                expand=expand,
                notify=notify,
                notify_author=notify_author,
            ),
        )
        return self._decode(Entity, data)


def _build_deadline(
    deadline: EntityDeadline | datetime | date | str | None,
) -> dict[str, Any] | None:
    """Render a deadline as the `{"date", "deadlineType"}` object the API expects.

    An `EntityDeadline` (e.g. one read from another item) is rendered by
    the model itself and keeps its own `deadline_type`; a bare date,
    timestamp or ready-made API string is sent as type `date`. A
    deadline without a date is left out entirely.

    Every checklist page of the documentation shows the date as a full
    `YYYY-MM-DDThh:mm:ss.sss±hhmm` timestamp, so a bare `date` is sent
    as midnight UTC. Pass a timezone-aware `datetime` when the offset
    matters.
    """
    if deadline is None:
        return None

    if isinstance(deadline, EntityDeadline):
        if deadline.date is None:
            return None
        payload = deadline._render(as_timestamp=True)  # noqa: SLF001
        payload.setdefault("deadlineType", "date")
        return payload

    return {"date": to_tracker_datetime(deadline), "deadlineType": "date"}


def _checklist_item_payload(
    *,
    text: str | None,
    checked: bool | None,
    assignee: str | int | None,
    deadline: EntityDeadline | datetime | date | str | None,
) -> dict[str, Any]:
    """Build the body of a single checklist item; `None` fields are left out."""
    payload: dict[str, Any] = {}
    if text is not None:
        payload["text"] = text
    if checked is not None:
        payload["checked"] = checked
    if assignee is not None:
        payload["assignee"] = assignee
    built_deadline = _build_deadline(deadline)
    if built_deadline is not None:
        payload["deadline"] = built_deadline
    return payload


def _checklist_items_payload(
    items: Iterable[EntityChecklistItem | dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert the items of `edit_entity_checklist` to the plain dicts the API wants.

    An `EntityChecklistItem` is re-encoded into the request shape by its
    own `_to_request` hook, so the same item renders identically here
    and anywhere else it reaches a request body (`update_entity`, for
    instance). A dict passes through verbatim: the caller then owns the
    exact body.
    """
    checked = _check_sequence(items, "items", "checklist items", "item")
    payload = [_convert_value(item) for item in checked]
    if not payload:
        msg = "At least one checklist item is required."
        raise ValueError(msg)
    return payload
