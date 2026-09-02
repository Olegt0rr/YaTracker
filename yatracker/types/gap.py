from __future__ import annotations

__all__ = ["Gap", "GapsResult", "GapsSearchResult", "UserGaps"]

from datetime import datetime

from .base import Base, field
from .user import FullUser


class Gap(Base):
    """Absence record of an employee (vacation, sick leave, duty, ...).

    `workflow` is one of `vacation`, `paid_day_off`, `illness`,
    `absence`, `trip`, `conference_trip`, `conference`, `learning`,
    `maternity` or `duty`; the up-to-date list is served by
    `GET /v3/gaps/workflows`. The value is not validated client-side.

    Attributes
    ----------
    id - Absence record ID.
    workflow - Absence type.
    from_ - Start of the absence (sent and returned as `from`).
    to - End of the absence.
    full_day - Whether the absence takes the whole day.
    work_in_absence - Whether the employee works during the absence.
    user - Employee the record belongs to. Returned by `POST /gaps`;
    the search endpoint groups the records by user instead and leaves
    this field out.

    Source:
    https://yandex.ru/support/tracker/ru/api/gaps/post-gaps

    """

    id: str
    workflow: str
    from_: datetime = field(alias="from")
    to: datetime
    full_day: bool
    work_in_absence: bool
    user: FullUser | None = None


class UserGaps(Base):
    """Absence records of a single employee.

    Attributes
    ----------
    user - The employee.
    gaps - Absence records of the employee inside the requested time
    window. Empty when the employee has none.

    Source:
    https://yandex.ru/support/tracker/ru/api/gaps/search-gaps

    """

    user: FullUser
    gaps: list[Gap] = field(default_factory=list)


class GapsSearchResult(Base):
    """One page of absence records, grouped by employee.

    Attributes
    ----------
    user_gaps - One entry per requested employee.
    has_more - Whether more pages are available.

    Source:
    https://yandex.ru/support/tracker/ru/api/gaps/search-gaps

    """

    user_gaps: list[UserGaps] = field(default_factory=list)
    has_more: bool = False


class GapsResult(Base):
    """Envelope `POST /gaps` answers with.

    Attributes
    ----------
    gaps - Absence records that were actually saved (outdated records
    are not included).

    Source:
    https://yandex.ru/support/tracker/ru/api/gaps/post-gaps

    """

    gaps: list[Gap] = field(default_factory=list)
