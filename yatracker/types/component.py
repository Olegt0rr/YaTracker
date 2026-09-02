from __future__ import annotations

__all__ = ["Component", "ComponentRef"]

from .base import Base, field
from .queue import Queue
from .ref import Ref
from .user import User


class ComponentRef(Ref):
    """Short component reference embedded into queue and issue objects.

    Issue payloads carry only `self`, `id` and `display` for every
    component (see the issue response fields reference). The shape of
    `components` in `GET /queues/{id}?expand=components` is not
    documented; it is assumed to be the same by analogy with `versions`.
    Should the API embed full objects there, only these three fields are
    kept — use `get_queue_components` for the full ones.
    """


class Component(Base):
    """Represents Component.

    Attributes
    ----------
    url - Reference to the object.
    id - Component ID.
    version - Component version. Each change of the component
    increments the version number.
    name - Component name.
    queue - Queue the component belongs to.
    description - Component description.
    lead - Component owner.
    assign_auto - Flag of the automatic assignment of the component
    owner as the assignee of new issues with this component.

    """

    url: str = field(alias="self")
    id: str
    version: int
    name: str
    queue: Queue
    description: str | None = None
    lead: User | None = None
    assign_auto: bool | None = None
