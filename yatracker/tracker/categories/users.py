from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
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
        when the API reports no next page. The docs describe the `id`
        cursor as the user the next page *starts from*, so if the cursor
        user comes back at the top of a page it is not yielded twice.

        Source:
        https://yandex.ru/support/tracker/ru/api/users/get-users-relative

        :param per_page: number of users per page (1 to 100).
        :param expand: additional fields to include in the response:
            "groups" - the groups the users belong to.
        """
        id_: str | None = None
        while True:
            page = await self.get_users_relative(
                per_page=per_page,
                id_=id_,
                expand=expand,
            )
            users = page.users
            # A page that does not advance past the cursor would be
            # requested again forever (and re-yield users already seen
            # on the previous page): stop before yielding anything,
            # even if `hasNext` is true.
            if not users or users[-1].uid == id_:
                return

            for user in users:
                if user.uid != id_:
                    yield user

            if not page.has_next:
                return

            id_ = users[-1].uid

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
