from __future__ import annotations

__all__ = [
    "Entity",
    "EntityChecklistItem",
    "EntityDeadline",
    "EntityEvent",
    "EntityEventChange",
    "EntityEventField",
    "EntityEvents",
    "EntityFields",
    "EntityKeyResult",
    "EntityKeyResultProgress",
    "EntityLink",
    "EntityMetricItem",
    "EntityParent",
    "EntityRef",
    "EntitySearchResult",
    "EntityType",
]

# `date` is aliased: `EntityDeadline` has a field named `date`, which would
# otherwise shadow the class while the annotations are being evaluated.
from datetime import date as date_
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from .attachment import Attachment
from .base import Base, field
from .queue import Queue
from .user import User

if TYPE_CHECKING:
    from collections.abc import Sequence

EntityType = Literal["project", "portfolio", "goal"]
"""Kind of entity: a project, a portfolio of projects or a goal."""


class EntityRef(Base):
    """Short reference to an entity, embedded into `parentEntity`."""

    url: str = field(alias="self")
    id: str
    display: str | None = None


class EntityParent(Base):
    """Parent entities of an entity (`parentEntity` field)."""

    primary: EntityRef | None = None
    secondary: list[EntityRef] = field(default_factory=list)


class EntityDeadline(Base):
    """Deadline of a checklist item or a key result."""

    date: date_ | None = None
    deadline_type: str | None = None
    is_exceeded: bool | None = None


class EntityChecklistItem(Base):
    """Single item of the entity checklist (`checklistItems` field)."""

    id: str
    text: str | None = None
    text_html: str | None = None
    checked: bool | None = None
    assignee: User | None = None
    deadline: EntityDeadline | None = None
    checklist_item_type: str | None = None


class EntityMetricItem(Base):
    """Single metric of an entity (`metricItems` field)."""

    id: str
    text: str | None = None
    url: str | None = None


class EntityKeyResultProgress(Base):
    """Progress of a key result: start, target and current values."""

    start: float | None = None
    end: float | None = None
    current: float | None = None


class EntityKeyResult(Base):
    """Single key result of a goal (`keyResultItems` field)."""

    id: str
    text: str | None = None
    type: str | None = None
    deadline: EntityDeadline | None = None
    progress: EntityKeyResultProgress | None = None
    achieved: bool | None = None
    assignee: User | None = None


class EntityFields(Base):
    """Fields of an entity (the `fields` object of an entity).

    The API returns only the fields listed in the `fields` query
    parameter, so every field here is optional. Unknown keys (custom
    fields and the ones not covered by the documentation) are kept as
    model extras and are reachable as attributes.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/about-entities
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
        coerce_numbers_to_str=True,
    )

    summary: str | None = None
    description: str | None = None
    author: User | None = None
    lead: User | None = None
    team_users: list[User] | None = None
    clients: list[User] | None = None
    followers: list[User] | None = None
    start: date_ | datetime | None = None
    end: date_ | datetime | None = None
    quarter: list[str] | None = None
    tags: list[str] | None = None
    parent_entity: EntityParent | None = None
    team_access: bool | None = None
    entity_status: str | None = None
    issue_queues: list[Queue] | None = None
    checklist_items: list[EntityChecklistItem] | None = None
    metric_items: list[EntityMetricItem] | None = None
    key_result_items: list[EntityKeyResult] | None = None
    progress_percentage: float | None = None
    last_comment_updated_at: date_ | datetime | None = None
    linked_goals_count: int | None = None
    linked_projects_count: int | None = None


class EntityLink(Base):
    """Link between an entity and another entity or issue.

    :param relationship: "depends on", "is dependent by",
        "works towards", "parent entity", "child entity"
        or "is supported by".
    :param entity: id of the linked entity (or key of the linked issue).
    """

    relationship: str
    entity: str


class Entity(Base):
    """Project, portfolio or goal (`/entities` API).

    These are the projects of the current Tracker interface, unlike the
    legacy `/projects` API.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/about-entities
    """

    url: str = field(alias="self")
    id: str
    version: int
    short_id: int
    entity_type: str
    created_by: User
    created_at: datetime
    updated_at: datetime | None = None
    attachments: list[Attachment] | None = None
    fields: EntityFields = field(default_factory=EntityFields)

    async def refresh(
        self,
        *,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Get the current state of the entity."""
        return await self._tracker.get_entity(
            self.entity_type,
            self.id,
            fields=fields,
            expand=expand,
        )

    async def update(
        self,
        *,
        values: dict[str, Any] | None = None,
        comment: str | None = None,
        links: Sequence[EntityLink | dict[str, Any]] | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Entity:
        """Edit the entity."""
        return await self._tracker.update_entity(
            self.entity_type,
            self.id,
            values=values,
            comment=comment,
            links=links,
            fields=fields,
            expand=expand,
            **kwargs,
        )

    async def delete(self, *, with_board: bool | None = None) -> None:
        """Delete the entity."""
        return await self._tracker.delete_entity(
            self.entity_type,
            self.id,
            with_board=with_board,
        )

    async def get_events(self, **kwargs) -> EntityEvents:
        """Get the change history of the entity."""
        return await self._tracker.get_entity_events(
            self.entity_type,
            self.id,
            **kwargs,
        )


class EntitySearchResult(Base):
    """Page of entities returned by `POST /entities/<type>/_search`."""

    hits: int
    pages: int
    values: list[Entity] = field(default_factory=list)
    order_by: str | None = None


class EntityEventField(Base):
    """Field changed by an entity event."""

    id: str
    display: str | None = None


class EntityEventChange(Base):
    """Single field change of an entity event."""

    diff: str | None = None
    field: EntityEventField | None = None


class EntityEvent(Base):
    """Single event of the entity change history."""

    id: str
    author: User | None = None
    date: datetime
    transport: str | None = None
    display: str | None = None
    changes: list[EntityEventChange] = field(default_factory=list)


class EntityEvents(Base):
    """Page of the entity change history."""

    events: list[EntityEvent] = field(default_factory=list)
    has_next: bool = False
    has_prev: bool = False
