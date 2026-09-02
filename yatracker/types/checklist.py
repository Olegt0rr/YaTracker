from __future__ import annotations

__all__ = ["ChecklistAssignee", "ChecklistDeadline", "ChecklistItem"]

from datetime import datetime

from .base import Base


class ChecklistDeadline(Base):
    """Deadline of a checklist item.

    Attributes
    ----------
    date - Deadline date and time.
    deadline_type - Type of the deadline (`date`).
    is_exceeded - Flag showing that the deadline has passed.

    """

    date: datetime
    deadline_type: str
    is_exceeded: bool | None = None


class ChecklistAssignee(Base):
    """Assignee of a checklist item.

    The checklist item assignee is a trimmed-down user object: unlike
    :class:`~yatracker.types.user.User` it carries no `self` reference,
    so it cannot be replaced with the regular user model.

    Attributes
    ----------
    id - User ID.
    display - Displayed user name.
    passport_uid - Unique ID of the user's Yandex account.
    login - User login.
    first_name - User first name.
    last_name - User last name.
    email - User email address.
    tracker_uid - Unique ID of the user's Tracker account.

    """

    id: str
    display: str
    passport_uid: int | None = None
    login: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    tracker_uid: int | None = None


class ChecklistItem(Base):
    """Represents a checklist item of an issue.

    Attributes
    ----------
    id - Checklist item ID.
    text - Text of the checklist item.
    checked - Flag showing that the item is marked as done.
    text_html - Text of the checklist item in HTML format.
    assignee - Assignee of the checklist item.
    deadline - Deadline of the checklist item.
    checklist_item_type - Type of the checklist item.

    """

    id: str
    text: str
    checked: bool
    text_html: str | None = None
    assignee: ChecklistAssignee | None = None
    deadline: ChecklistDeadline | None = None
    checklist_item_type: str | None = None
