from __future__ import annotations

from typing import Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.queue_permissions import (
    ComponentGroupAccess,
    ComponentUserAccess,
    QueueAccessUpdate,
    QueueGroupAccess,
    QueuePermissions,
    QueueUserAccess,
)


class QueueAccess(BaseTracker):
    """Access rights of queues and their components."""

    async def get_queue_user_access(
        self,
        queue_id: str | int,
        user_id: str | int,
    ) -> QueueUserAccess:
        """Get the access rights of a user in a queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-user-access

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :param user_id: login or ID of the user.
        :return: permissions of the user in the queue and the
            components they have access to.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/permissions/users/{user_id}",
        )
        return self._decode(QueueUserAccess, data)

    async def get_queue_group_access(
        self,
        queue_id: str | int,
        group_id: str | int,
    ) -> QueueGroupAccess:
        """Get the access rights of a group in a queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-group-access

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :param group_id: ID of the group in the organization.
        :return: permissions of the group in the queue and the
            components it has access to.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/permissions/groups/{group_id}",
        )
        return self._decode(QueueGroupAccess, data)

    async def update_queue_access(  # noqa: PLR0913
        self,
        queue_id: str | int,
        *,
        create: QueueAccessUpdate | dict[str, Any] | None = None,
        read: QueueAccessUpdate | dict[str, Any] | None = None,
        write: QueueAccessUpdate | dict[str, Any] | None = None,
        grant: QueueAccessUpdate | dict[str, Any] | None = None,
        deny: QueueAccessUpdate | dict[str, Any] | None = None,
    ) -> QueuePermissions:
        """Grant access rights to a queue.

        Every permission takes a :class:`QueueAccessUpdate` (or the
        equivalent dict) listing the users, groups and roles it applies
        to. A plain list of ids overwrites the current grantees of that
        kind, a :class:`~yatracker.types.QueueAccessChange`
        (`{"add": [...], "remove": [...]}`) adds and revokes them.
        Permissions left as ``None`` are not sent, i.e. they stay
        unchanged; at least one of them must be given.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/manage-access

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :param create: grantees of the permission to create issues.
        :param read: grantees of the permission to read issues.
        :param write: grantees of the permission to edit issues.
        :param grant: grantees of the permission to change the queue
            settings.
        :param deny: grantees denied access to the queue. Roles cannot
            be denied, only users and groups.
        :return: access rights of the queue after the update.
        """
        payload = self._prepare_payload(locals(), exclude=["queue_id"])
        data = await self._client.request(
            method="PATCH",
            uri=f"/queues/{queue_id}/permissions",
            payload=payload,
        )
        return self._decode(QueuePermissions, data)

    async def get_component_user_access(
        self,
        component_id: str | int,
        user_id: str | int,
    ) -> ComponentUserAccess:
        """Get the access rights of a user to a component.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-component-user-access

        :param component_id: ID of the component.
        :param user_id: login or ID of the user.
        :return: permissions of the user for the component.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/components/{component_id}/permissions/users/{user_id}",
        )
        return self._decode(ComponentUserAccess, data)

    async def get_component_group_access(
        self,
        component_id: str | int,
        group_id: str | int,
    ) -> ComponentGroupAccess:
        """Get the access rights of a group to a component.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-component-group-access

        :param component_id: ID of the component.
        :param group_id: ID of the group in the organization.
        :return: permissions of the group for the component.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/components/{component_id}/permissions/groups/{group_id}",
        )
        return self._decode(ComponentGroupAccess, data)
