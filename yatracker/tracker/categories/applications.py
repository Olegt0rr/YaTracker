from __future__ import annotations

from yatracker.tracker.base import BaseTracker
from yatracker.types import Application


class Applications(BaseTracker):
    async def get_applications(self) -> list[Application]:
        """Get external applications.

        Use this request to get a list of external applications
        a remote link can be created with.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-applications

        :return: list of external applications.
        """
        data = await self._client.request(
            method="GET",
            uri="/applications",
        )
        return self._decode(list[Application], data)
