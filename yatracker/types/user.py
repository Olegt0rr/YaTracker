from __future__ import annotations

__all__ = ["FullUser", "User", "UsersPage"]

from datetime import datetime

from .base import Base, field, url_field
from .ref import Ref


class User(Base):
    """Short user reference embedded into other API objects.

    Issues, queues, comments and the like carry only `self`, `id` and
    `display` for a user. Use :class:`FullUser` (returned by the
    `/users` and `/myself` endpoints) for the whole account.
    """

    url: str = url_field()
    id: str
    display: str


class FullUser(Base):
    """User account of the organization.

    Returned by `GET /myself`, `GET /users/{login_or_id}`,
    `GET /users` and `GET /users/_relative`. This is not a subclass of
    :class:`User`: the account payload is keyed by `uid` and carries no
    `id` field in the API reference.

    Attributes
    ----------
    url - Reference to the user account.
    uid - Unique ID of the user account in Tracker.
    login - User login.
    display - Name of the user displayed in the interface.
    id - User ID. Not listed in the reference for these endpoints (the
    account is addressed by `uid`), kept optional for the payloads that
    do carry it, e.g. short user references reused as a `FullUser`.
    tracker_uid - Unique ID of the user account in Tracker.
    passport_uid - Unique ID of the user account in Yandex 360 for
    Business / Yandex ID.
    cloud_uid - Unique ID of the user in Yandex Identity Hub.
    first_name - First name of the user.
    last_name - Last name of the user.
    email - Email of the user.
    groups - Groups the user belongs to. Only returned when the request
    is made with `expand="groups"`, `None` otherwise.
    external - Service parameter.
    has_license - Whether the user has full access to Tracker
    (`False` means read-only).
    dismissed - Whether the user was removed from the organization.
    use_new_filters - Service parameter.
    disable_notifications - Whether notifications are forcibly disabled
    for the user.
    first_login_date - Date and time of the first login to Tracker.
    last_login_date - Date and time of the last login to Tracker.
    welcome_mail_sent - How the user was added: `True` with an email
    invitation, `False` some other way.
    sources - Data sources of the account, e.g. `["directory"]` for the
    corporate directory. Documented for the relative pagination
    endpoint only.
    position - Job position of the user. Documented for the relative
    pagination endpoint only and absent from the response samples.

    """

    url: str = url_field()
    uid: str
    login: str
    display: str

    id: str | None = None
    tracker_uid: str | None = None
    passport_uid: str | None = None
    cloud_uid: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    groups: list[Ref] | None = None
    external: bool | None = None
    has_license: bool | None = None
    dismissed: bool | None = None
    use_new_filters: bool | None = None
    disable_notifications: bool | None = None
    first_login_date: datetime | None = None
    last_login_date: datetime | None = None
    welcome_mail_sent: bool | None = None
    sources: list[str] | None = None
    position: str | None = None


class UsersPage(Base):
    """Page of users returned by the relative pagination endpoint.

    Attributes
    ----------
    users - Users of the current page, sorted by `uid` ascending.
    has_next - Whether more pages are available.

    """

    users: list[FullUser] = field(default_factory=list)
    has_next: bool = False
