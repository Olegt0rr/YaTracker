from __future__ import annotations

__all__ = ["Transition"]

from .base import Base, url_field
from .status import Status


class Transition(Base):
    id: str
    url: str = url_field()
    display: str
    to: Status

    async def execute(self) -> None:
        """Execute transition."""
        await self._tracker.execute_transition(self)
