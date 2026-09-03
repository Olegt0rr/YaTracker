from __future__ import annotations

__all__ = [
    "EntityAccessChange",
    "EntityAccessGrantees",
    "EntityAccessRule",
    "EntityAcl",
    "EntityPermissions",
]

from typing import Any

from .base import Base, field
from .entity import EntityParent, EntityRef
from .ref import Ref
from .user import User

EntityGrantee = str | int | dict[str, Any]
"""One grantee of an access rule.

A user is addressed by login, by numeric id or by an object naming the
id to use (`{"uid": 123}`, `{"login": "username"}`), a group by its
numeric id and a role by its name.
"""


class EntityAccessRule(Base):
    """Users, groups and roles one access type applies to.

    The value of a `READ` / `WRITE` / `GRANT` key of the `grant` or
    `revoke` object of `update_entity_access`. Every field accepts a
    single value as well as a list of them; the fields left as `None`
    are not sent.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/patch-access

    Attributes
    ----------
    users - Logins or ids of the users the access type applies to.
    groups - Ids of the groups the access type applies to.
    roles - Roles the access type applies to: `AUTHOR`, `OWNER`,
    `CLIENT`, `FOLLOWER` or `MEMBER`.

    """

    users: list[EntityGrantee] | EntityGrantee | None = None
    groups: list[int | str] | int | str | None = None
    roles: list[str] | str | None = None


class EntityAccessChange(Base):
    """Access types to grant to (or revoke from) users, groups and roles.

    The `grant` / `revoke` object of `update_entity_access`. The access
    types left as `None` are not sent.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/patch-access

    Attributes
    ----------
    read - Grantees of the permission to view the entity (`READ`).
    write - Grantees of the permission to edit the entity (`WRITE`).
    grant - Grantees of the permission to change the access settings of
    the entity (`GRANT`).

    """

    read: EntityAccessRule | None = field(default=None, alias="READ")
    write: EntityAccessRule | None = field(default=None, alias="WRITE")
    grant: EntityAccessRule | None = field(default=None, alias="GRANT")


class EntityAccessGrantees(Base):
    """Users, groups and roles holding one access type.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/get-access

    Attributes
    ----------
    users - Users holding the access type personally.
    groups - Groups holding the access type.
    roles - Roles holding the access type: `AUTHOR`, `OWNER`, `CLIENT`,
    `FOLLOWER` or `MEMBER`.

    """

    users: list[User] = field(default_factory=list)
    groups: list[Ref] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)


class EntityAcl(Base):
    """Access types of an entity and who holds them.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/get-access

    Attributes
    ----------
    read - Who may view the entity (`READ`).
    write - Who may edit the entity (`WRITE`).
    grant - Who may change the access settings of the entity (`GRANT`).

    """

    read: EntityAccessGrantees | None = field(default=None, alias="READ")
    write: EntityAccessGrantees | None = field(default=None, alias="WRITE")
    grant: EntityAccessGrantees | None = field(default=None, alias="GRANT")


class EntityPermissions(Base):
    """Access settings of a project, a portfolio or a goal.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/get-access

    Attributes
    ----------
    acl - Users, groups and roles holding each access type. Empty while
    the entity inherits its access settings, i.e. while
    `permission_sources` is not empty.
    permission_sources - Entity the access settings are inherited from:
    the primary portfolio of a project or a portfolio, or the parent
    goal of a goal.
    parent_entities - Parent entities of the entity: the primary one
    and, for projects and portfolios, the additional portfolios.

    """

    acl: EntityAcl = field(default_factory=EntityAcl)
    permission_sources: list[EntityRef] = field(default_factory=list)
    parent_entities: EntityParent | None = None
