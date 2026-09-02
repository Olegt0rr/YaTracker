from __future__ import annotations

__all__ = ["FullIssue"]

from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeVar, overload

from typing_extensions import Self

from yatracker.utils.datetime import to_tracker_datetime

from .base import Base, url_field
from .checklist import ChecklistItem
from .comment import Comment
from .component import ComponentRef
from .issue import Issue
from .issue_type import IssueType
from .priority import Priority
from .queue import Queue
from .sprint import Sprint
from .status import Status
from .transitions import Transitions
from .user import User

if TYPE_CHECKING:
    import builtins

    from .changelog import Changelog
    from .issue_link import IssueLink, LinkRelationship

IssueT = TypeVar("IssueT", bound="FullIssue")


def _render_deadline(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Render a `datetime` deadline before delegating to the tracker.

    Done here so the naive-datetime warning points at the caller of the
    `FullIssue` helper, not at the frames below it.
    """
    if isinstance(kwargs.get("deadline"), datetime):
        kwargs["deadline"] = to_tracker_datetime(kwargs["deadline"], stacklevel=4)
    return kwargs


class FullIssue(Base):
    url: str = url_field()
    id: str
    key: str
    version: int

    summary: str
    parent: Issue | None = None
    description: str | None = None
    sprint: list[Sprint] | None = None
    components: list[ComponentRef] | None = None
    checklist_items: list[ChecklistItem] | None = None
    checklist_total: int | None = None
    checklist_done: int | None = None
    type: IssueType
    priority: Priority
    followers: list[User] | None = None
    queue: Queue
    previous_queue: Queue | None = None
    favorite: bool
    assignee: User | None = None

    last_comment_update_at: datetime | None = None
    aliases: list[str] | None = None
    updated_by: User | None = None
    created_at: datetime
    created_by: User
    votes: int
    updated_at: datetime | None = None
    status: Status
    previous_status: Status | None = None
    direction: str | None = None

    async def get_transitions(self) -> Transitions:
        """Return dict and list-like Transitions object.

        Iterate Transitions like a list:
        >>> transitions = await self.get_transitions()
        >>> for t in transitions:
        >>>    print(t)

        Use Transitions like a dict with transition names:
        >>> transitions = await self.get_transitions()
        >>> close = transitions.get('close')
        >>> if close:
        >>>    await close.execute()
        """
        return await self._tracker.get_transitions(self.id)

    async def get_comments(self) -> list[Comment]:
        """Get comments for self.

        :return:
        """
        return await self._tracker.get_comments(self.id)

    async def post_comment(self, text: str, **kwargs) -> Comment:
        """Post comment for self."""
        return await self._tracker.post_comment(self.id, text=text, **kwargs)

    async def get_checklist(self) -> list[ChecklistItem]:
        """Get the checklist of self."""
        return await self._tracker.get_checklist(self.id)

    @overload
    async def add_checklist_item(
        self,
        text: str,
        *,
        _type: builtins.type[IssueT],
        **kwargs,
    ) -> IssueT: ...

    @overload
    async def add_checklist_item(self, text: str, **kwargs) -> Self: ...

    async def add_checklist_item(
        self,
        text: str,
        *,
        _type: builtins.type[FullIssue] | None = None,
        **kwargs,
    ) -> FullIssue:
        """Add an item to the checklist of self.

        The result is decoded as `type(self)` unless `_type` is given
        (e.g. `_type=FullIssue` when the subclass requires fields the
        checklist response does not carry).

        :return: the updated issue.
        """
        return await self._tracker.add_checklist_item(
            self.id,
            text,
            _type=_type or type(self),
            **_render_deadline(kwargs),
        )

    @overload
    async def edit_checklist_item(
        self,
        item_id: str,
        text: str,
        *,
        _type: builtins.type[IssueT],
        **kwargs,
    ) -> IssueT: ...

    @overload
    async def edit_checklist_item(
        self,
        item_id: str,
        text: str,
        **kwargs,
    ) -> Self: ...

    async def edit_checklist_item(
        self,
        item_id: str,
        text: str,
        *,
        _type: builtins.type[FullIssue] | None = None,
        **kwargs,
    ) -> FullIssue:
        """Edit an item of the checklist of self.

        The API requires `text` even when only `checked` has to be
        toggled, so pass the current text of the item to keep it.

        The result is decoded as `type(self)` unless `_type` is given
        (e.g. `_type=FullIssue` when the subclass requires fields the
        checklist response does not carry).

        :return: the updated issue.
        """
        return await self._tracker.edit_checklist_item(
            self.id,
            item_id,
            text,
            _type=_type or type(self),
            **_render_deadline(kwargs),
        )

    @overload
    async def delete_checklist_item(
        self,
        item_id: str,
        *,
        _type: builtins.type[IssueT],
    ) -> IssueT: ...

    @overload
    async def delete_checklist_item(self, item_id: str) -> Self: ...

    async def delete_checklist_item(
        self,
        item_id: str,
        *,
        _type: builtins.type[FullIssue] | None = None,
    ) -> FullIssue:
        """Delete an item from the checklist of self.

        The result is decoded as `type(self)` unless `_type` is given.

        :return: the updated issue.
        """
        return await self._tracker.delete_checklist_item(
            self.id,
            item_id,
            _type=_type or type(self),
        )

    @overload
    async def delete_checklist(self, *, _type: builtins.type[IssueT]) -> IssueT: ...

    @overload
    async def delete_checklist(self) -> Self: ...

    async def delete_checklist(
        self,
        *,
        _type: builtins.type[FullIssue] | None = None,
    ) -> FullIssue:
        """Delete the whole checklist of self.

        The result is decoded as `type(self)` unless `_type` is given.

        :return: the updated issue.
        """
        return await self._tracker.delete_checklist(
            self.id,
            _type=_type or type(self),
        )

    async def get_links(self) -> list[IssueLink]:
        """Get issue links."""
        return await self._tracker.get_issue_links(self.id)

    async def link(
        self,
        relationship: LinkRelationship | str,
        issue: str | Issue,
    ) -> IssueLink:
        """Create a link between self and another issue.

        :param relationship: type of the link, e.g. "relates"
            (see `LinkRelationship`).
        :param issue: ID or key of the issue to link.
        :return: the created link.
        """
        return await self._tracker.link_issues(self.id, relationship, issue)

    async def unlink(self, link_id: str | int) -> bool:
        """Delete a link between self and another issue.

        :param link_id: ID of the link.
        :return: `True` if the link was deleted.
        """
        return await self._tracker.unlink_issues(self.id, link_id)

    async def get_changelog(
        self,
        *,
        id_: str | None = None,
        per_page: int | None = None,
        field: str | None = None,
        type_: str | None = None,
    ) -> list[Changelog]:
        """Get one page of the change history of self.

        :param id_: id of the change the requested ones follow.
        :param per_page: number of changes per page (50 by default).
        :param field: id of the changed issue field to filter by.
        :param type_: key of the change type to filter by.
        """
        return await self._tracker.get_issue_changelog(
            self.id,
            id_=id_,
            per_page=per_page,
            field=field,
            type_=type_,
        )
