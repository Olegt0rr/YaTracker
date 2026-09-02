from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker, _iter_relative, _relative_page_size
from yatracker.types.user import FullUser, UsersPage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class Users(BaseTracker):
    async def get_users(  # noqa: PLR0913
        self,
        per_page: int | None = None,
        page: int | None = None,
        *,
        id_: str | int | None = None,
        email: str | None = None,
        group: str | int | None = None,
        expand: str | None = None,
    ) -> list[FullUser]:
        """Get the users of the organization.

        The response is paginated and the endpoint returns at most
        10 000 users; use :meth:`get_users_relative` or
        :meth:`iter_users` for bigger organizations.

        Source:
        https://yandex.ru/support/tracker/ru/api/users/get-users

        :param per_page: number of users per page (1 to 100).
        :param page: page number (1 by default).
        :param id_: uid of the user to start the search from
            (query param "id").
        :param email: return the user with this email only.
        :param group: return the users of this group only.
        :param expand: additional fields to include in the response:
            "groups" - the groups the users belong to.
        :return: list of users.
        """
        params = self._prepare_params(
            per_page=per_page,
            page=page,
            id_=id_,
            email=email,
            group=group,
            expand=expand,
        )
        data = await self._client.request(
            method="GET",
            uri="/users",
            params=params,
        )
        return self._decode(list[FullUser], data)

    async def get_users_relative(
        self,
        per_page: int | None = None,
        id_: str | int | None = None,
        expand: str | None = None,
    ) -> UsersPage:
        """Get one page of users (relative pagination).

        Unlike :meth:`get_users`, this endpoint is not capped at 10 000
        users. Users are sorted by `uid` in ascending order, so the next
        page is requested with the uid of the last user of the current
        one; `UsersPage.has_next` tells whether more pages are left.

        Source:
        https://yandex.ru/support/tracker/ru/api/users/get-users-relative

        :param per_page: number of users per page (1 to 100).
        :param id_: uid of the user to start the search from
            (query param "id"). Omit it to get the first page.
        :param expand: additional fields to include in the response:
            "groups" - the groups the users belong to.
        :return: page of users.
        """
        params = self._prepare_params(
            per_page=per_page,
            id_=id_,
            expand=expand,
        )
        data = await self._client.request(
            method="GET",
            uri="/users/_relative",
            params=params,
        )
        return self._decode(UsersPage, data)

    async def iter_users(
        self,
        per_page: int | None = None,
        expand: str | None = None,
    ) -> AsyncIterator[FullUser]:
        """Iterate over all users of the organization, page by page.

        Wraps :meth:`get_users_relative`: every page is requested with
        the uid of the last user of the previous one and iteration stops
        when the API reports no next page (see
        :func:`yatracker.tracker.base._iter_relative`).

        Source:
        https://yandex.ru/support/tracker/ru/api/users/get-users-relative

        :param per_page: number of users per page (1 to 100).
            `per_page=1` is sent as 2: the cursor user is resent on
            every page, so a page of one could never advance.
        :param expand: additional fields to include in the response:
            "groups" - the groups the users belong to.
        """
        page_size = _relative_page_size(per_page)

        async def fetch_page(id_: str | None) -> UsersPage:
            return await self.get_users_relative(
                per_page=page_size,
                id_=id_,
                expand=expand,
            )

        async for user in _iter_relative(
            fetch_page,
            items=lambda page: page.users,
            key=lambda user: user.uid,
            has_next=lambda page: page.has_next,
        ):
            yield user

    async def get_user(
        self,
        user_id: str | int,
        expand: str | None = None,
    ) -> FullUser:
        """Get a user of the organization.

        Source:
        https://yandex.ru/support/tracker/ru/api/users/get-user

        :param user_id: uid or login of the user. A login made of digits
            only has to be prefixed with `login:` (`"login:12345"`),
            otherwise it is treated as a uid.
        :param expand: additional fields to include in the response:
            "groups" - the groups the user belongs to.
        :return: user.
        """
        params = self._prepare_params(expand=expand)
        data = await self._client.request(
            method="GET",
            uri=f"/users/{user_id}",
            params=params,
        )
        return self._decode(FullUser, data)

    async def get_myself(self, expand: str | None = None) -> FullUser:
        """Get the current user.

        Returns the account the API requests are made on behalf of.

        Source:
        https://yandex.ru/support/tracker/ru/api/users/get-user-info

        :param expand: additional fields to include in the response:
            "groups" - the groups the user belongs to.
        :return: current user.
        """
        params = self._prepare_params(expand=expand)
        data = await self._client.request(
            method="GET",
            uri="/myself",
            params=params,
        )
        return self._decode(FullUser, data)
