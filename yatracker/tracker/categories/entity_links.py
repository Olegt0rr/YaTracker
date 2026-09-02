from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from yatracker.tracker.base import BaseTracker
from yatracker.types.entity import EntityLinkInfo, EntityType

from .entities import _entity_uri, _fields_params

if TYPE_CHECKING:
    from collections.abc import Sequence


class EntityLinks(BaseTracker):
    """Links between projects, portfolios and goals (`/entities`).

    A parent entity is not a link: set the `parentEntity` field with
    `update_entity` instead.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/links/get-links
    """

    async def get_entity_links(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        fields: str | Sequence[str] | None = None,
    ) -> list[EntityLinkInfo]:
        """Get the links of an entity to other entities.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/links/get-links

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param fields: Fields of the linked entities to return (a
            comma-separated string or a sequence of names), e.g.
            `"id,summary"`. Without it the links come back with an empty
            `link_field_values`.
        :return: List of links of the entity.
        """
        data = await self._client.request(
            method="GET",
            uri=_entity_uri(entity_type, str(entity_id), "links"),
            params=_fields_params(fields),
        )
        return self._decode(list[EntityLinkInfo], data)

    async def link_entities(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        relationship: str,
        entity: str | int | Sequence[str | int],
    ) -> bool:
        """Link an entity to one or several other entities.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/links/add-links

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity to link from.
        :param relationship: Kind of the link. For projects and
            portfolios: "depends on" (the entity depends on the linked
            one), "is dependent by" (the entity blocks the linked one)
            or "works towards" (a link of a project to a goal). For
            goals: "parent entity", "child entity", "depends on",
            "is dependent by" or "is supported by" (a link to a
            project).
        :param entity: Id of the entity to link to, or a sequence of
            ids to create several links with the same `relationship` at
            once.
        :raises ValueError: If `entity` is an empty sequence.
        :return: `True` if the links were created. The API documents no
            response body for this request.
        """
        payload: dict[str, Any] | list[dict[str, Any]]
        if isinstance(entity, (str, int)):
            payload = {"relationship": relationship, "entity": str(entity)}
        else:
            payload = [
                {"relationship": relationship, "entity": str(item)} for item in entity
            ]
            if not payload:
                msg = "At least one entity to link to is required."
                raise ValueError(msg)

        await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type, str(entity_id), "links"),
            # the body may be a JSON array; `request` serialises whatever
            # it is given, only its annotation is narrower
            payload=cast("dict[str, Any]", payload),
        )
        return True

    async def delete_entity_link(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        right: str | int,
    ) -> bool:
        """Delete the link between two entities.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/links/delete-link

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity to unlink.
        :param right: Id of the entity the link is deleted with.
        :return: `True` if the link was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=_entity_uri(entity_type, str(entity_id), "links"),
            params={"right": str(right)},
        )
        return True
