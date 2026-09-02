from __future__ import annotations

__all__ = ["FieldRef", "Macro", "MacroFieldChange"]

from typing import Any

from pydantic import field_validator

from .base import Base, field
from .queue import Queue
from .ref import Ref


class FieldRef(Ref):
    """Short issue-field reference embedded into macro payloads.

    Attributes
    ----------
    url - Reference to the object.
    id - Field ID.
    display - Field name displayed in the interface.

    """


class MacroFieldChange(Base):
    """One entry of `Macro.issue_update`.

    Attributes
    ----------
    field - Issue field changed by the macro.
    update - Operation applied to the field, e.g. `{"add": ["tag 1"]}`,
    `{"set": "value"}` or `{"remove": ["tag 2"]}`. The docs only show
    the operator-object form; the value is kept untyped so that a plain
    value or `null` echoed back by the API does not break decoding.

    """

    field: FieldRef
    update: Any = None


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

    @field_validator("issue_update", mode="before")
    @classmethod
    def _none_as_empty(cls, value: Any) -> Any:  # noqa: ANN401
        """Treat an explicit `null` like an absent `issueUpdate`."""
        return [] if value is None else value

    def issue_update_payload(self) -> dict[str, Any]:
        """Return the field changes in the request format.

        The API returns `issueUpdate` as a list of `{field, update}`
        objects but expects a dict keyed by field id in `create_macro` /
        `update_macro`. Use this to re-send (or extend) the existing
        changes:

            await tracker.update_macro(
                macro.queue.key,
                macro.id,
                macro.name,
                issue_update={
                    **macro.issue_update_payload(),
                    "tags": {"add": "new tag"},
                },
            )
        """
        return {change.field.id: change.update for change in self.issue_update}
