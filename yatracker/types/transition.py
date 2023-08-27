from __future__ import annotations

__all__ = ["Transition"]

from .base import Base, field
from .status import Status


class Transition(Base, kw_only=True):
    id: str
    url: str = field(name="self")
    display: str
    to: Status

    async def execute(self) -> None:
        """Execute transition."""
        await self._tracker.execute_transition(self)
