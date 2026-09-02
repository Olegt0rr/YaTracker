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
    "EntityLinkInfo",
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
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import AliasChoices, BeforeValidator, ConfigDict, TypeAdapter

from .attachment import Attachment
from .base import Base, field, url_field
from .queue import Queue
from .user import User

if TYPE_CHECKING:
    from collections.abc import Sequence

EntityType = Literal["project", "portfolio", "goal"]
"""Kind of entity: a project, a portfolio of projects or a goal."""

_DATE_ADAPTER = TypeAdapter(date_)
_DATETIME_ADAPTER = TypeAdapter(datetime)


def _parse_date_or_datetime(value: Any) -> Any:  # noqa: ANN401
    """Pick the type by the shape of the string, not by its value.

    A plain union would decide by validation mode and by the value
    itself: in python mode a midnight timestamp is happily coerced to a
    bare `date`, losing both the time and the offset. Parsing is left to
    pydantic, because `datetime.fromisoformat` rejects `+0000` and `Z`
    on Python 3.10.
    """
    if isinstance(value, str):
        has_time = "T" in value or " " in value.strip()
        return (_DATETIME_ADAPTER if has_time else _DATE_ADAPTER).validate_python(value)
    return value


DateOrDatetime = Annotated[date_ | datetime, BeforeValidator(_parse_date_or_datetime)]
"""A field the API returns either as `YYYY-MM-DD` or as a full timestamp."""


class EntityRef(Base):
    """Short reference to an entity, embedded into `parentEntity`."""

    url: str = url_field()
    id: str
    display: str | None = None


class EntityParent(Base):
    """Parent entities of an entity (`parentEntity` field)."""

    primary: EntityRef | None = None
    secondary: list[EntityRef] = field(default_factory=list)


class EntityDeadline(Base):
    """Deadline of a checklist item or a key result.

    The API documents `date` as a full timestamp
    (`YYYY-MM-DDThh:mm:ss.sss±hhmm`) for checklist items and as a plain
    `YYYY-MM-DD` date for key results, so it is read as whichever of the
    two the response actually carries. `deadline_type` is `date` or
    `quarter`.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/about-entities
    """

    date: DateOrDatetime | None = None
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
    # the API key is `url`; the field is named `link` because in this
    # library `url` is reserved for the `self` link of an object
    link: str | None = field(default=None, alias="url")


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
    model extras: the ones whose name is a valid Python identifier are
    reachable as attributes (`fields.customField`), while local-field
    ids like `"64a51c6d866ea82411abe756--userId"` are not and have to be
    read through `fields.model_extra["..."]` or `getattr`.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/about-entities
    """

    # The rest of the config (alias generator, `populate_by_name`,
    # `coerce_numbers_to_str`) is inherited from `Base`: pydantic merges
    # the parent config into this one.
    model_config = ConfigDict(extra="allow")

    # not part of the `fields` block of an entity, but `fields=id` is a
    # valid selector for `linkFieldValues` of `get_entity_links`
    id: str | None = None
    summary: str | None = None
    description: str | None = None
    author: User | None = None
    lead: User | None = None
    team_users: list[User] | None = None
    clients: list[User] | None = None
    followers: list[User] | None = None
    start: DateOrDatetime | None = None
    end: DateOrDatetime | None = None
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
    last_comment_updated_at: DateOrDatetime | None = None
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


class EntityLinkInfo(Base):
    """Link of an entity, as returned by `GET /entities/<type>/<id>/links`.

    The response sample names the kind of the link `type` while the
    parameter table calls it `relationship`, so both keys are accepted
    and the value is exposed as `relationship`, like in
    :class:`EntityLink`.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/links/get-links

    Attributes
    ----------
    relationship - Kind of the link: "depends on", "is dependent by",
    "works towards", "parent entity", "child entity" or
    "is supported by".
    link_field_values - Fields of the linked entity: the ones listed in
    the `fields` parameter of the request, so everything is optional.

    """

    relationship: str | None = field(
        default=None,
        validation_alias=AliasChoices("type", "relationship"),
        serialization_alias="relationship",
    )
    link_field_values: EntityFields = field(default_factory=EntityFields)


class Entity(Base):
    """Project, portfolio or goal (`/entities` API).

    These are the projects of the current Tracker interface, unlike the
    legacy `/projects` API.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/about-entities
    """

    url: str = url_field()
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

    async def delete(self, *, with_board: bool | None = None) -> bool:
        """Delete the entity.

        :return: `True` if the entity was deleted.
        """
        return await self._tracker.delete_entity(
            self.entity_type,
            self.id,
            with_board=with_board,
        )

    async def get_events(
        self,
        *,
        per_page: int | None = None,
        from_: str | None = None,
        selected: str | None = None,
        new_events_on_top: bool | None = None,
        direction: str | None = None,
    ) -> EntityEvents:
        """Get the change history of the entity.

        :param per_page: Number of events per page (50 by default).
        :param from_: Id of the event to count the page from. Mutually
            exclusive with `selected`.
        :param selected: Id of the event to place in the middle of the
            page. Mutually exclusive with `from_`.
        :param new_events_on_top: Whether to sort the newest events first.
        :param direction: "forward" or "backward".
        :raises ValueError: If both `from_` and `selected` are given.
        """
        return await self._tracker.get_entity_events(
            self.entity_type,
            self.id,
            per_page=per_page,
            from_=from_,
            selected=selected,
            new_events_on_top=new_events_on_top,
            direction=direction,
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
