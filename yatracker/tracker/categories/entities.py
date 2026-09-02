from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, get_args

from yatracker.tracker.base import BaseTracker, _convert_value, _encode_key
from yatracker.types import BulkChange
from yatracker.types.entity import (
    Entity,
    EntityEvents,
    EntityLink,
    EntitySearchResult,
    EntityType,
)
from yatracker.utils.datetime import to_tracker_date, to_tracker_datetime

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Sequence

ENTITY_TYPES: tuple[str, ...] = get_args(EntityType)


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
        :param links: Links to other entities, either `EntityLink`
            objects or dicts like
            `{"relationship": "works towards", "entity": "1234"}`.
        :param fields: Fields to return in the response (a
            comma-separated string or a sequence of names).
        :param kwargs: Extra fields merged on top of `values`, encoded
            the same way. `None` values are dropped; to clear a field,
            pass it via `values`.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/create-entity
        """
        payload: dict[str, Any] = {
            "fields": _prepare_fields({"summary": summary, **(values or {})}, kwargs),
        }
        prepared_links = _prepare_links(links)
        if prepared_links:
            payload["links"] = prepared_links

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
        :param links: Links to add, either `EntityLink` objects or dicts.
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
        payload: dict[str, Any] = {}

        prepared_fields = _prepare_fields(values, kwargs)
        if prepared_fields:
            payload["fields"] = prepared_fields

        if comment is not None:
            payload["comment"] = comment

        prepared_links = _prepare_links(links)
        if prepared_links:
            payload["links"] = prepared_links

        if not payload:
            msg = (
                "Entity update requires at least one field (passed via "
                "`values` or as a keyword argument), a comment or a link."
            )
            raise ValueError(msg)

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
    ) -> None:
        """Delete an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param with_board: Whether to delete the board of the entity.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/delete-entity
        """
        params = None if with_board is None else {"withBoard": str(with_board).lower()}
        await self._client.request(
            method="DELETE",
            uri=_entity_uri(entity_type, str(entity_id)),
            params=params,
        )

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

        params = _fields_params(fields)
        if per_page is not None:
            params = {**(params or {}), "perPage": str(per_page)}
        if page is not None:
            params = {**(params or {}), "page": str(page)}

        data = await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type, "_search"),
            params=params,
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
        :param links: Links to add, either `EntityLink` objects or dicts.
        :param kwargs: Extra fields merged on top of `values`.
        :raises ValueError: If there are no entities or nothing to change.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/bulkchange-entities
        """
        meta_entities = [
            entity if isinstance(entity, str) else entity.id for entity in entities
        ]
        if not meta_entities:
            msg = "At least one entity is required."
            raise ValueError(msg)

        changes: dict[str, Any] = {}

        prepared_fields = _prepare_fields(values, kwargs)
        if prepared_fields:
            changes["fields"] = prepared_fields

        if comment is not None:
            changes["comment"] = comment

        prepared_links = _prepare_links(links)
        if prepared_links:
            changes["links"] = prepared_links

        if not changes:
            msg = (
                "Bulk update requires at least one field (passed via "
                "`values` or as a keyword argument), a comment or a link."
            )
            raise ValueError(msg)

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
    """Build the uri of an entities endpoint, validating the entity type."""
    if entity_type not in ENTITY_TYPES:
        msg = (
            f"Unknown entity type {entity_type!r}. "
            f"Expected one of: {', '.join(ENTITY_TYPES)}."
        )
        raise ValueError(msg)
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


def _prepare_fields(
    values: dict[str, Any] | None,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Merge explicit `values` with the fields passed as keyword arguments.

    Top-level keys of both sources are encoded the same way, so a field
    passed twice ends up as a single key with the `kwargs` value winning.
    `None` keyword arguments are dropped, like in `bulk_update_issues`.
    """
    prepared = {
        _encode_key(key): _convert_entity_value(value)
        for key, value in (values or {}).items()
    }
    prepared.update(
        {
            _encode_key(key): _convert_entity_value(value)
            for key, value in kwargs.items()
            if value is not None
        },
    )
    return prepared


def _prepare_links(
    links: Sequence[EntityLink | dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Convert links to the plain dicts the API expects."""
    return [_convert_value(link) for link in links or ()]


def _convert_entity_value(obj: Any) -> Any:  # noqa: ANN401
    """Convert a field value to a basic type, rendering dates as the API wants."""
    match obj:
        case datetime():
            return to_tracker_datetime(obj, stacklevel=5)
        case date():
            return to_tracker_date(obj)
        case list():
            return [_convert_entity_value(item) for item in obj]
        case dict():
            return {key: _convert_entity_value(value) for key, value in obj.items()}
        case _:
            return _convert_value(obj)
