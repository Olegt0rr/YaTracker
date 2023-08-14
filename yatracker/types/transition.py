from __future__ import annotations

__all__ = ["Transition"]

from .base import Base, field
from .status import Status


class Transition(Base, kw_only=True, frozen=True):
    id: str = field(name="self")
    url: str
    display: str
    to: Status

    async def execute(self) -> None:
        """Execute transition."""
        await self.tracker.execute_transition(self)
