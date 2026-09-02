from __future__ import annotations

import warnings
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker, _convert_value, _encode_key
from yatracker.types import BulkChange
from yatracker.types.entity import (
    Entity,
    EntityEvents,
    EntityLink,
    EntitySearchResult,
    EntityType,
)
from yatracker.utils.datetime import (
    NAIVE_DATETIME_WARNING,
    to_tracker_date,
    to_tracker_datetime,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence


class Entities(BaseTracker):
    """Projects, portfolios and goals API (`/entities`).

    These are the projects of the current Tracker interface (with
    statuses, portfolios, goals and checklists), unlike the legacy
    `/projects` API.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/about-entities
    """

    async def create_entity(
        self,
        entity_type: EntityType,
        summary: str,
        *,
        values: dict[str, Any] | None = None,
        links: Sequence[EntityLink | dict[str, Any]] | None = None,
        fields: str | Sequence[str] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Entity:
        """Create an entity (a project, a portfolio or a goal).

        :param entity_type: "project", "portfolio" or "goal".
        :param summary: Name of the entity.
        :param values: Fields of the entity, e.g.
            `{"entityStatus": "in_progress"}`. Snake_case keys are
            converted to camelCase; keys that are not Python identifiers
            (local field ids like `"<id>--name"`) are sent as is.
            `date`/`datetime` values are rendered the way the API
            expects them.
        :param links: Links to other entities: a sequence of
            `EntityLink` objects or of dicts like
            `{"relationship": "works towards", "entity": "1234"}`.
            A single link on its own raises `TypeError`.
        :param fields: Fields to return in the response (a
            comma-separated string or a sequence of names).
        :param kwargs: Extra fields merged on top of `values`, encoded
            the same way. `None` values are dropped; to clear a field,
            pass it via `values`.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/create-entity
        """
        payload = _entity_changes(
            {"summary": summary, **(values or {})},
            kwargs,
            links=links,
            required=False,
        )

        data = await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type),
            params=_fields_params(fields),
            payload=payload,
        )
        return self._decode(Entity, data)

    async def get_entity(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Get an entity by its id.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param fields: Fields to return in the response (a
            comma-separated string or a sequence of names).
        :param expand: Additional information to include,
            e.g. "attachments".

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/get-entity
        """
        data = await self._client.request(
            method="GET",
            uri=_entity_uri(entity_type, str(entity_id)),
            params=_fields_params(fields, expand=expand),
        )
        return self._decode(Entity, data)

    async def update_entity(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        values: dict[str, Any] | None = None,
        comment: str | None = None,
        links: Sequence[EntityLink | dict[str, Any]] | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> Entity:
        """Edit an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param values: Fields to set, encoded like in `create_entity`.
        :param comment: Comment to add to the entity.
        :param links: Links to add: a sequence of `EntityLink` objects
            or of dicts. A single link on its own raises `TypeError`.
        :param fields: Fields to return in the response.
        :param expand: Additional information to include,
            e.g. "attachments".
        :param kwargs: Extra fields merged on top of `values`.
        :raises ValueError: If there is nothing to change.

        A version conflict (412), a locked entity (423) and unmet
        preconditions (428) come back as a generic `YaTrackerError`.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/update-entity
        """
        payload = _entity_changes(values, kwargs, comment=comment, links=links)

        data = await self._client.request(
            method="PATCH",
            uri=_entity_uri(entity_type, str(entity_id)),
            params=_fields_params(fields, expand=expand),
            payload=payload,
        )
        return self._decode(Entity, data)

    async def delete_entity(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        with_board: bool | None = None,
    ) -> bool:
        """Delete an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param with_board: Whether to delete the board of the entity.
        :return: `True` if the entity was deleted.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/delete-entity
        """
        params = None if with_board is None else {"withBoard": str(with_board).lower()}
        await self._client.request(
            method="DELETE",
            uri=_entity_uri(entity_type, str(entity_id)),
            params=params,
        )
        return True

    async def search_entities(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        *,
        query: str | None = None,
        filter_: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        fields: str | Sequence[str] | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> EntitySearchResult:
        """Find entities matching the given criteria.

        :param entity_type: "project", "portfolio" or "goal".
        :param query: Substring of the entity name (sent as `input`).
        :param filter_: Field filters, e.g.
            `{"entityStatus": "in_progress", "followers": "notEmpty()"}`.
            Keys are encoded like in `create_entity`.
        :param order_by: Field to sort the result by.
        :param order_asc: Sort direction: ascending if `True`.
        :param root_only: Whether to return only the entities without
            a parent entity.
        :param fields: Fields to return in the response.
        :param per_page: Number of entities per page (50 by default).
        :param page: Page number (1 by default).

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/search-entities
        """
        payload: dict[str, Any] = {}
        if query is not None:
            payload["input"] = query
        if filter_:
            payload["filter"] = _prepare_fields(filter_, {})
        if order_by is not None:
            payload["orderBy"] = order_by
        if order_asc is not None:
            payload["orderAsc"] = order_asc
        if root_only is not None:
            payload["rootOnly"] = root_only

        params: dict[str, str] = {**(_fields_params(fields) or {})}
        if per_page is not None:
            params["perPage"] = str(per_page)
        if page is not None:
            params["page"] = str(page)

        data = await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type, "_search"),
            params=params or None,
            payload=payload,
        )
        return self._decode(EntitySearchResult, data)

    async def iter_entities(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        *,
        query: str | None = None,
        filter_: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        root_only: bool | None = None,
        fields: str | Sequence[str] | None = None,
        per_page: int | None = None,
    ) -> AsyncIterator[Entity]:
        """Iterate over all entities matching the given criteria.

        Pages through :meth:`search_entities` until the last page is
        reached or a page comes back empty.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/search-entities
        """
        page = 1
        while True:
            result = await self.search_entities(
                entity_type,
                query=query,
                filter_=filter_,
                order_by=order_by,
                order_asc=order_asc,
                root_only=root_only,
                fields=fields,
                per_page=per_page,
                page=page,
            )
            if not result.values:
                return

            for entity in result.values:
                yield entity

            if page >= result.pages:
                return

            page += 1

    async def bulk_update_entities(
        self,
        entity_type: EntityType,
        entities: Sequence[str | Entity],
        *,
        values: dict[str, Any] | None = None,
        comment: str | None = None,
        links: Sequence[EntityLink | dict[str, Any]] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> BulkChange:
        """Edit multiple entities at once.

        The operation is performed in the background: the returned
        `BulkChange` is the usual bulk change object, so
        `get_bulk_change`, `wait_bulk_change` and `BulkChange.wait()`
        work for it as well.

        :param entity_type: "project", "portfolio" or "goal".
        :param entities: Sequence of entity ids (or `Entity` objects).
        :param values: Fields to set, encoded like in `create_entity`.
        :param comment: Comment to add to every entity.
        :param links: Links to add: a sequence of `EntityLink` objects
            or of dicts.
        :param kwargs: Extra fields merged on top of `values`.
        :raises TypeError: If `entities` or `links` is a bare value
            instead of a sequence.
        :raises ValueError: If there are no entities or nothing to change.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/bulkchange-entities
        """
        meta_entities = _prepare_meta_entities(entities)
        changes = _entity_changes(values, kwargs, comment=comment, links=links)

        data = await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type, "bulkchange", "_update"),
            payload={"metaEntities": meta_entities, "values": changes},
        )
        return self._decode(BulkChange, data)

    async def get_entity_events(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        per_page: int | None = None,
        from_: str | None = None,
        selected: str | None = None,
        new_events_on_top: bool | None = None,
        direction: str | None = None,
    ) -> EntityEvents:
        """Get the change history of an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param per_page: Number of events per page (50 by default).
        :param from_: Id of the event to count the page from. Mutually
            exclusive with `selected`.
        :param selected: Id of the event to place in the middle of the
            page. Mutually exclusive with `from_`.
        :param new_events_on_top: Whether to sort the newest events first.
        :param direction: "forward" or "backward".
        :raises ValueError: If both `from_` and `selected` are given.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/get-events-relative
        """
        if from_ is not None and selected is not None:
            msg = "Pass either `from_` or `selected`, not both."
            raise ValueError(msg)

        params: dict[str, str] = {}
        if per_page is not None:
            params["perPage"] = str(per_page)
        if from_ is not None:
            params["from"] = from_
        if selected is not None:
            params["selected"] = selected
        if new_events_on_top is not None:
            params["newEventsOnTop"] = str(new_events_on_top).lower()
        if direction is not None:
            params["direction"] = direction

        data = await self._client.request(
            method="GET",
            uri=_entity_uri(entity_type, str(entity_id), "events", "_relative"),
            params=params or None,
        )
        return self._decode(EntityEvents, data)


def _entity_uri(entity_type: str, *parts: str) -> str:
    """Build the uri of an entities endpoint.

    The entity type is not validated at runtime: `EntityType` documents
    the kinds Tracker has today, but `Entity.entity_type` comes back from
    the server as a plain string, so a kind added later still works.
    """
    return "/".join(("/entities", entity_type, *parts))


def _fields_params(
    fields: str | Sequence[str] | None,
    *,
    expand: str | None = None,
) -> dict[str, str] | None:
    """Build the `fields`/`expand` query params."""
    params: dict[str, str] = {}
    if fields:
        params["fields"] = fields if isinstance(fields, str) else ",".join(fields)
    if expand:
        params["expand"] = expand
    return params or None


def _entity_changes(
    values: dict[str, Any] | None,
    kwargs: dict[str, Any],
    *,
    comment: str | None = None,
    links: Sequence[EntityLink | dict[str, Any]] | None = None,
    required: bool = True,
) -> dict[str, Any]:
    """Build the `fields`/`comment`/`links` body shared by the write methods.

    Empty parts are left out entirely. When `required` is set (every
    method but `create_entity`, which always has a summary), an empty
    result means the caller asked for nothing and raises `ValueError`.
    """
    changes: dict[str, Any] = {}

    # stacklevel=4: the warning is raised inside `_prepare_fields`, so it is
    # _prepare_fields -> this function -> the public method -> user code
    prepared_fields = _prepare_fields(values, kwargs, stacklevel=4)
    if prepared_fields:
        changes["fields"] = prepared_fields

    if comment is not None:
        changes["comment"] = comment

    prepared_links = _prepare_links(links)
    if prepared_links:
        changes["links"] = prepared_links

    if required and not changes:
        msg = (
            "This operation requires at least one field (passed via "
            "`values` or as a keyword argument), a comment or a link."
        )
        raise ValueError(msg)

    return changes


def _prepare_meta_entities(entities: Sequence[str | Entity]) -> list[str]:
    """Convert a sequence of entities into a list of entity ids."""
    if isinstance(entities, str):
        msg = (
            "This endpoint accepts only a sequence of entity ids. "
            "A bare string would be iterated character by character."
        )
        raise TypeError(msg)

    meta_entities = [
        entity if isinstance(entity, str) else entity.id for entity in entities
    ]
    if not meta_entities:
        msg = "At least one entity is required."
        raise ValueError(msg)
    return meta_entities


def _prepare_fields(
    values: dict[str, Any] | None,
    kwargs: dict[str, Any],
    *,
    stacklevel: int = 3,
) -> dict[str, Any]:
    """Merge explicit `values` with the fields passed as keyword arguments.

    Top-level keys of both sources are encoded the same way, so a field
    passed twice ends up as a single key with the `kwargs` value winning.
    `None` keyword arguments are dropped, like in `bulk_update_issues`.

    A naive `datetime` anywhere in the merged values is reported once,
    from here: warning per value would point at a comprehension frame or
    at a recursive call instead of at the user's code. `stacklevel`
    should point at that call site: the default `3` is this helper ->
    the public method (`search_entities`) -> user code, plus one for
    every extra frame in between.
    """
    merged = {
        **(values or {}),
        **{key: value for key, value in kwargs.items() if value is not None},
    }
    if _has_naive_datetime(merged):
        warnings.warn(NAIVE_DATETIME_WARNING, UserWarning, stacklevel=stacklevel)

    return {
        _encode_key(key): _convert_entity_value(value) for key, value in merged.items()
    }


def _prepare_links(
    # The bare types are part of the annotation only so that the runtime
    # guard below is not dead code for a type checker: a single link is
    # exactly the kind of value that would otherwise be iterated.
    links: Sequence[EntityLink | dict[str, Any]]
    | EntityLink
    | dict[str, Any]
    | str
    | None,
) -> list[dict[str, Any]]:
    """Convert links to the plain dicts the API expects."""
    if isinstance(links, (str, dict, EntityLink)):
        msg = (
            f"`links` must be a sequence of links, got {type(links).__name__}. "
            "Pass a sequence of links, e.g. `[link]`."
        )
        raise TypeError(msg)
    return [_convert_value(link) for link in links or ()]


def _has_naive_datetime(obj: Any) -> bool:  # noqa: ANN401
    """Tell whether a value contains a naive `datetime` at any depth."""
    match obj:
        case datetime():
            return obj.utcoffset() is None
        case dict():
            return any(_has_naive_datetime(value) for value in obj.values())
        case list() | tuple() | set() | frozenset():
            return any(_has_naive_datetime(item) for item in obj)
        case _:
            return False


def _convert_entity_value(obj: Any) -> Any:  # noqa: ANN401
    """Convert a field value to a basic type, rendering dates as the API wants.

    Naive datetimes are reported by `_prepare_fields`, so the rendering
    helper is asked to stay quiet here.
    """
    match obj:
        case datetime():
            return to_tracker_datetime(obj, warn=False)
        case date():
            return to_tracker_date(obj)
        case list() | tuple() | set() | frozenset():
            return [_convert_entity_value(item) for item in obj]
        case dict():
            return {key: _convert_entity_value(value) for key, value in obj.items()}
        case _:
            return _convert_value(obj)
