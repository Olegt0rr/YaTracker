from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

from yatracker.tracker.base import BaseTracker, IssueT_co
from yatracker.types import ChecklistItem, FullIssue
from yatracker.utils.datetime import to_tracker_datetime

if TYPE_CHECKING:
    from datetime import datetime


def _build_payload(
    *,
    text: str,
    checked: bool | None,
    assignee: str | int | None,
    deadline: str | None,
) -> dict[str, Any]:
    """Build a checklist item payload, skipping unset fields.

    `checked=False` is a meaningful value and is sent as is; only
    ``None`` means "leave it out".
    """
    payload: dict[str, Any] = {"text": text}
    if checked is not None:
        payload["checked"] = checked
    if assignee is not None:
        payload["assignee"] = str(assignee)
    if deadline is not None:
        payload["deadline"] = {"date": deadline, "deadlineType": "date"}
    return payload


class Checklists(BaseTracker):
    async def get_checklist(self, issue_id: str) -> list[ChecklistItem]:
        """Get the checklist of an issue.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/issues/get-checklist

        :param issue_id: ID or key of the issue.
        :return: list of checklist items.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/checklistItems",
        )
        return self._decode(list[ChecklistItem], data)

    @overload
    async def add_checklist_item(
        self,
        issue_id: str,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: datetime | str | None = None,
    ) -> FullIssue: ...

    @overload
    async def add_checklist_item(
        self,
        issue_id: str,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: datetime | str | None = None,
        _type: type[IssueT_co] = ...,
    ) -> IssueT_co: ...

    async def add_checklist_item(
        self,
        issue_id: str,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: datetime | str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
    ) -> IssueT_co | FullIssue:
        """Add an item to the checklist of an issue.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/issues/add-checklist-item

        :param issue_id: ID or key of the issue.
        :param text: text of the checklist item.
        :param checked: mark the item as done.
        :param assignee: login or ID of the checklist item assignee.
        :param deadline: deadline of the checklist item. A timezone-aware
            `datetime` is rendered the way the API expects; a string is
            sent verbatim, so a ready-made API value may be passed.
        :param _type: you can use your own extended FullIssue type.

        Fields left as ``None`` are not sent.

        :return: the whole issue (not the created item).
        """
        payload = _build_payload(
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=to_tracker_datetime(deadline),
        )
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/checklistItems",
            payload=payload,
        )
        return self._decode(_type, data)

    @overload
    async def edit_checklist_item(
        self,
        issue_id: str,
        item_id: str,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: datetime | str | None = None,
    ) -> FullIssue: ...

    @overload
    async def edit_checklist_item(
        self,
        issue_id: str,
        item_id: str,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: datetime | str | None = None,
        _type: type[IssueT_co] = ...,
    ) -> IssueT_co: ...

    async def edit_checklist_item(  # noqa: PLR0913
        self,
        issue_id: str,
        item_id: str,
        text: str,
        *,
        checked: bool | None = None,
        assignee: str | int | None = None,
        deadline: datetime | str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
    ) -> IssueT_co | FullIssue:
        """Edit an item of the checklist of an issue.

        The API requires `text` even when only `checked` has to be
        toggled, so pass the current text of the item to keep it.

        Attention: the official documentation shows the request body
        wrapped in a JSON array, but the API (and the official
        `yandex_tracker_client`) expects a plain object, which is what
        is sent here.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/issues/edit-checklist

        :param issue_id: ID or key of the issue.
        :param item_id: ID of the checklist item to edit.
        :param text: text of the checklist item.
        :param checked: mark the item as done.
        :param assignee: login or ID of the checklist item assignee.
        :param deadline: deadline of the checklist item. A timezone-aware
            `datetime` is rendered the way the API expects; a string is
            sent verbatim, so a ready-made API value may be passed.
        :param _type: you can use your own extended FullIssue type.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: the whole issue (not the edited item).
        """
        payload = _build_payload(
            text=text,
            checked=checked,
            assignee=assignee,
            deadline=to_tracker_datetime(deadline),
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}/checklistItems/{item_id}",
            payload=payload,
        )
        return self._decode(_type, data)

    @overload
    async def delete_checklist_item(
        self,
        issue_id: str,
        item_id: str,
    ) -> FullIssue: ...

    @overload
    async def delete_checklist_item(
        self,
        issue_id: str,
        item_id: str,
        *,
        _type: type[IssueT_co] = ...,
    ) -> IssueT_co: ...

    async def delete_checklist_item(
        self,
        issue_id: str,
        item_id: str,
        *,
        _type: type[IssueT_co | FullIssue] = FullIssue,
    ) -> IssueT_co | FullIssue:
        """Delete an item from the checklist of an issue.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/issues/delete-checklist-item

        :param issue_id: ID or key of the issue.
        :param item_id: ID of the checklist item to delete.
        :param _type: you can use your own extended FullIssue type.
        :return: the whole issue with the remaining checklist items.
        """
        data = await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/checklistItems/{item_id}",
        )
        return self._decode(_type, data)

    @overload
    async def delete_checklist(self, issue_id: str) -> FullIssue: ...

    @overload
    async def delete_checklist(
        self,
        issue_id: str,
        *,
        _type: type[IssueT_co] = ...,
    ) -> IssueT_co: ...

    async def delete_checklist(
        self,
        issue_id: str,
        *,
        _type: type[IssueT_co | FullIssue] = FullIssue,
    ) -> IssueT_co | FullIssue:
        """Delete the whole checklist of an issue.

        Source:
        https://yandex.cloud/ru/docs/tracker/concepts/issues/delete-checklist

        :param issue_id: ID or key of the issue.
        :param _type: you can use your own extended FullIssue type.
        :return: the whole issue without the checklist.
        """
        data = await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/checklistItems",
        )
        return self._decode(_type, data)
