from __future__ import annotations

from yatracker.tracker.base import BaseTracker
from yatracker.types import Priority


class Priorities(BaseTracker):
    # ruff: noqa: FBT001 FBT002
    async def get_priorities(self, localized: bool = True) -> list[Priority]:
        """Get priorities.

        Use this request to get a list of priorities for an issue.
        """
        params = {"localized": str(localized).lower()} if localized else None
        data = await self._client.request(
            method="GET",
            uri="/priorities",
            params=params,
        )
        return self._decode(list[Priority], data)
