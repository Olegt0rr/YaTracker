from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker, _convert_value
from yatracker.types.entity import EntityType
from yatracker.types.entity_access import EntityAccessChange, EntityPermissions

from .entities import _entity_uri

if TYPE_CHECKING:
    from collections.abc import Sequence


class EntityAccess(BaseTracker):
    """Access settings of projects, portfolios and goals (`/entities`).

    The `/extendedPermissions` endpoints used here also carry
    `permissionSources`, the entity the access settings are inherited
    from. The plain `/permissions` endpoints of the same page do not,
    and their body is the `acl` object on its own.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/get-access
    """

    async def get_entity_access(
        self,
        entity_type: EntityType,
        entity_id: str | int,
    ) -> EntityPermissions:
        """Get the access settings of an entity.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/get-access

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :return: Users, groups and roles holding each access type, plus
            the entity the access settings are inherited from.
        """
        data = await self._client.request(
            method="GET",
            uri=_entity_uri(entity_type, str(entity_id), "extendedPermissions"),
        )
        return self._decode(EntityPermissions, data)

    async def update_entity_access(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        grant: EntityAccessChange | dict[str, Any] | None = None,
        revoke: EntityAccessChange | dict[str, Any] | None = None,
        permission_sources: str | Sequence[str] | None = None,
    ) -> EntityPermissions:
        """Grant or revoke access to an entity.

        While the entity inherits its access settings from a parent one,
        `grant` and `revoke` have no effect and the `teamAccess` field
        of the entity is ignored: pass `permission_sources=[]` first (in
        the same request or in an earlier one) to stop inheriting.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/patch-access

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param grant: Access types to grant, as an
            `EntityAccessChange` or the equivalent dict, e.g.
            `{"READ": {"users": ["username"]}}`.
        :param revoke: Access types to revoke, in the same shape as
            `grant`.
        :param permission_sources: Id of the entity to inherit the
            access settings from (the primary portfolio of a project or
            a portfolio, the parent goal of a goal). An empty sequence
            stops inheriting. To change the parent entity itself, use
            `update_entity`.
        :raises ValueError: If there is nothing to change.
        :return: Access settings of the entity after the update.
        """
        payload: dict[str, Any] = {}
        if permission_sources is not None:
            payload["permissionSources"] = (
                permission_sources
                if isinstance(permission_sources, str)
                else list(permission_sources)
            )

        acl: dict[str, Any] = {}
        if grant is not None:
            acl["grant"] = _convert_value(grant)
        if revoke is not None:
            acl["revoke"] = _convert_value(revoke)
        if acl:
            payload["acl"] = acl

        if not payload:
            msg = "This operation requires `grant`, `revoke` or `permission_sources`."
            raise ValueError(msg)

        data = await self._client.request(
            method="PATCH",
            uri=_entity_uri(entity_type, str(entity_id), "extendedPermissions"),
            payload=payload,
        )
        return self._decode(EntityPermissions, data)
