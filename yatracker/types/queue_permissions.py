from __future__ import annotations

__all__ = [
    "ComponentGroupAccess",
    "ComponentUserAccess",
    "QueueAccessChange",
    "QueueAccessGrantees",
    "QueueAccessUpdate",
    "QueueGroupAccess",
    "QueuePermissions",
    "QueueUserAccess",
]

from .base import Base, field, url_field
from .component import Component, ComponentRef
from .ref import Ref
from .user import User


class QueueAccessChange(Base):
    """Permission change for one kind of grantee.

    The object form of a `users` / `groups` / `roles` entry of
    `PATCH /queues/{id}/permissions`: instead of overwriting the current
    grantees with a plain list of ids, it adds and revokes them.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/manage-access

    Attributes
    ----------
    add - Ids the permission is granted to.
    remove - Ids the permission is revoked from.

    """

    add: list[str | int] | None = None
    remove: list[str | int] | None = None


class QueueAccessUpdate(Base):
    """Grantees of one permission of `update_queue_access`.

    Every field takes either a plain list of ids (the current grantees
    of that kind are overwritten) or a :class:`QueueAccessChange`
    (grantees are added / revoked). At least one field must be set.

    Users are addressed by login, `uid`, `passportUid`, `cloudUid` or
    `trackerUid`, groups by their numeric id (see `GET /groups`) and
    roles by `author`, `assignee`, `follower` or `access`.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/manage-access

    Attributes
    ----------
    users - Users the permission applies to.
    groups - Groups the permission applies to.
    roles - Roles the permission applies to. Not allowed for `deny`:
    the API cannot forbid access to a role.

    """

    users: list[str | int] | QueueAccessChange | None = None
    groups: list[str | int] | QueueAccessChange | None = None
    roles: list[str] | QueueAccessChange | None = None


class QueueAccessGrantees(Base):
    """Users, groups and roles a single permission is granted to.

    Returned both as a value of the `permissions` mapping of the queue
    and component access requests, and as the `create` / `read` /
    `write` / `grant` / `deny` field of :class:`QueuePermissions`. The
    `self` link is only sent by the latter.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-user-access

    Attributes
    ----------
    url - Reference to the permission object.
    users - Users holding the permission personally.
    groups - Groups holding the permission.
    roles - Roles holding the permission.

    """

    url: str | None = field(
        default=None,
        validation_alias="self",
        serialization_alias="self",
    )
    users: list[User] | None = None
    groups: list[Ref] | None = None
    roles: list[Ref] | None = None


class QueuePermissions(Base):
    """Access rights of a queue, as returned by `update_queue_access`.

    Only the permissions that have grantees are sent back.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/manage-access

    Attributes
    ----------
    url - Reference to the permissions object.
    version - Version of the permissions. Every change increments it.
    create - Permission to create issues in the queue.
    read - Permission to read issues of the queue.
    write - Permission to edit issues of the queue.
    grant - Permission to change the queue settings.
    deny - Denied access to the queue.

    """

    url: str = url_field()
    version: int
    create: QueueAccessGrantees | None = None
    read: QueueAccessGrantees | None = None
    write: QueueAccessGrantees | None = None
    grant: QueueAccessGrantees | None = None
    deny: QueueAccessGrantees | None = None


class QueueUserAccess(Base):
    """Access rights of a user in a queue.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-user-access

    Attributes
    ----------
    user - User the request was made for.
    permissions - Permissions of the user in the queue, keyed by
    `GRANT` (queue settings), `CREATE` (create issues), `READ` (read
    issues), `WRITE` (edit issues) and `DENY` (access denied). Every
    value tells whether the permission comes from a personal grant, a
    group the user belongs to or a role.
    components - Components of the queue the user has access to.

    """

    user: User
    permissions: dict[str, QueueAccessGrantees]
    components: list[ComponentRef] | None = None


class QueueGroupAccess(Base):
    """Access rights of a group in a queue.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-group-access

    Attributes
    ----------
    group - Group the request was made for.
    permissions - Permissions of the group in the queue, keyed by
    `GRANT`, `CREATE`, `READ`, `WRITE` and `DENY`.
    components - Components of the queue the group has access to.

    """

    group: Ref
    permissions: dict[str, QueueAccessGrantees]
    components: list[ComponentRef] | None = None


class ComponentUserAccess(Base):
    """Access rights of a user to a component.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-component-user-access

    Attributes
    ----------
    user - User the request was made for.
    component - Component the request was made for.
    permissions - Permissions of the user for the component, keyed by
    `CREATE`, `READ`, `WRITE` and `DENY`.

    """

    user: User
    component: Component
    permissions: dict[str, QueueAccessGrantees]


class ComponentGroupAccess(Base):
    """Access rights of a group to a component.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-component-group-access

    Attributes
    ----------
    group - Group the request was made for.
    component - Component the request was made for.
    permissions - Permissions of the group for the component, keyed by
    `CREATE`, `READ`, `WRITE` and `DENY`.

    """

    group: Ref
    component: Component
    permissions: dict[str, QueueAccessGrantees]
