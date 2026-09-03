from __future__ import annotations

__all__ = [
    "Changelog",
    "ChangelogComments",
    "ChangelogExecutedTrigger",
    "ChangelogField",
]

from datetime import datetime
from typing import Any

from .base import Base, url_field
from .base import field as model_field
from .issue import Issue
from .ref import FieldRef, Ref
from .user import User


class ChangelogField(Base):
    """Single field change of a changelog record.

    Attributes
    ----------
    field - Reference to the changed issue field.
    from_ - Value of the field before the change (API key `from`).
    to - Value of the field after the change.

    `from_` and `to` are left untyped on purpose: the shape depends on
    the changed field. A single-valued field sends a string (e.g.
    `statusStartTime`), a multi-valued one sends a list of objects (e.g.
    `followers`), and an object-valued one sends `{self, id, key,
    display}` (e.g. `status`). `None` means the field was empty.

    """

    field: FieldRef
    from_: Any = model_field(default=None, alias="from")
    to: Any = None


class ChangelogComments(Base):
    """Comments touched by a changelog record.

    Only the `added` block is documented; other blocks the API may send
    for comment updates and removals are ignored.

    Attributes
    ----------
    added - References to the added comments. `display` carries the
    comment text.

    """

    added: list[Ref] | None = None


class ChangelogExecutedTrigger(Base):
    """Trigger fired by a changelog record.

    Attributes
    ----------
    trigger - Reference to the trigger.
    success - Whether the trigger ran successfully.
    message - Action performed when the trigger fired.

    """

    trigger: Ref
    success: bool | None = None
    message: str | None = None


class Changelog(Base):
    """Single record of the issue change history.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/get-changelog

    Attributes
    ----------
    url - Reference to the changelog record.
    id - ID of the change.
    issue - Issue the change belongs to.
    updated_at - Date and time of the change.
    updated_by - User who made the change.
    type - Type of the change, e.g. `IssueCreated`, `IssueUpdated`,
    `IssueMoved`, `IssueCloned`, `IssueCommentAdded`,
    `IssueCommentUpdated`, `IssueCommentRemoved`, `IssueWorklogAdded`,
    `IssueWorklogUpdated`, `IssueWorklogRemoved`,
    `IssueCommentReactionAdded`, `IssueCommentReactionRemoved`,
    `IssueVoteAdded`, `IssueVoteRemoved`, `IssueLinked`,
    `IssueLinkChanged`, `IssueUnlinked`,
    `RelatedIssueResolutionChanged`, `IssueAttachmentAdded`,
    `IssueAttachmentRemoved` or `IssueWorkflow`. The list is owned by
    the server, so the value is kept as a plain string.
    transport - Service parameter.
    fields - Changed issue fields.
    comments - Comments added by the change.
    executed_triggers - Triggers fired by the change.

    """

    url: str = url_field()
    id: str
    issue: Issue
    updated_at: datetime
    updated_by: User
    type: str
    transport: str | None = None
    fields: list[ChangelogField] | None = None
    comments: ChangelogComments | None = None
    executed_triggers: list[ChangelogExecutedTrigger] | None = None
