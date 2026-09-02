from __future__ import annotations

__all__ = ["Macro", "MacroFieldChange"]

from typing import Any

from .base import Base, field
from .field_ref import FieldRef
from .queue import Queue


class MacroFieldChange(Base):
    """One entry of `Macro.issue_update`.

    Attributes
    ----------
    field - Issue field changed by the macro.
    update - Operation applied to the field, e.g. `{"add": ["tag 1"]}`,
    `{"set": "value"}` or `{"remove": ["tag 2"]}`.

    """

    field: FieldRef
    update: dict[str, Any]


class Macro(Base):
    """Represents Macro.

    Attributes
    ----------
    url - Reference to the object.
    id - Macro ID.
    queue - Queue the macro belongs to.
    name - Macro name.
    body - Text of the comment added when the macro runs. Supports the
    `{{currentUser}}`, `{{currentDateTime}}` and `{{issue.author}}`
    placeholders.
    issue_update - Changes applied to the issue fields by the macro.

    """

    url: str = field(alias="self")
    id: str
    queue: Queue
    name: str
    body: str | None = None
    issue_update: list[MacroFieldChange] = field(default_factory=list)
