from __future__ import annotations

__all__ = ["Filter", "FilterPermission", "FilterPermissions", "FilterSort"]

from typing import Any

from .base import Base, field, url_field
from .ref import FieldRef, Ref
from .user import User


class FilterPermission(Base):
    """Subjects granted one kind of access (read or write) to a filter.

    Attributes
    ----------
    users - Users holding the permission.
    groups - Groups holding the permission.
    roles - Roles holding the permission. The shape of the objects is
    not documented (the samples always show an empty array), so they
    are kept as raw dicts.

    Source:
    https://yandex.ru/support/tracker/ru/api/filters/get-filter

    """

    users: list[User] = field(default_factory=list)
    groups: list[Ref] = field(default_factory=list)
    roles: list[dict[str, Any]] = field(default_factory=list)


class FilterPermissions(Base):
    """Access rights of a filter.

    The API keys the two blocks in upper case (`READ` and `WRITE`), so
    both fields carry an explicit alias.

    Attributes
    ----------
    read - Subjects allowed to read the filter.
    write - Subjects allowed to edit the filter.

    Source:
    https://yandex.ru/support/tracker/ru/api/filters/get-filter

    """

    read: FilterPermission | None = field(default=None, alias="READ")
    write: FilterPermission | None = field(default=None, alias="WRITE")


class FilterSort(Base):
    """One sorting rule of a filter.

    In responses `field` is an object; requests take the field key
    instead, e.g. `{"field": "created", "isAscending": False}`.

    Attributes
    ----------
    field - Issue field the result is sorted by.
    is_ascending - Sort direction: `True` ascending, `False` descending.

    Source:
    https://yandex.ru/support/tracker/ru/api/filters/update-filter

    """

    field: FieldRef
    is_ascending: bool | None = None

    def _to_request(self) -> dict[str, Any]:
        """Render the rule the way a request wants it.

        A response entry carries the whole field object while a request
        entry names the field by its key, so a rule read back from a
        filter can be passed straight into the next request.
        `is_ascending` is sent only when it is set.
        """
        encoded: dict[str, Any] = {"field": self.field.id}
        if self.is_ascending is not None:
            encoded["isAscending"] = self.is_ascending
        return encoded


class Filter(Base):
    """Saved issue filter.

    Attributes
    ----------
    url - Reference to the object.
    id - Filter ID.
    name - Filter name.
    filter_ - Filtering conditions keyed by issue field name, e.g.
    `{"status": "open", "assignee": "me()"}` (sent as `filter`).
    query - Filtering conditions written in the query language. A filter
    uses either `filter_` or `query`, never both.
    fields - Issue fields shown in the Tracker interface. Affects the
    interface only, not the result of `/issues/_search`.
    group_by - Issue field the result is grouped by in the interface.
    sorts - Sorting rules of the filter. Returned only when sorting is
    configured for the filter.
    favorite - Whether the filter is marked as a favorite.
    permissions - Access rights of the filter.
    owner - Owner of the filter.

    Source:
    https://yandex.ru/support/tracker/ru/api/filters/get-filter

    """

    url: str = url_field()
    id: str
    name: str
    filter_: dict[str, Any] | None = field(default=None, alias="filter")
    query: str | None = None
    fields: list[FieldRef] | None = None
    group_by: FieldRef | None = None
    sorts: list[FilterSort] | None = None
    favorite: bool | None = None
    permissions: FilterPermissions | None = None
    owner: User | None = None
