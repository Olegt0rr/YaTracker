from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yatracker.tracker import YaTracker


class TrackerAccess:
    @property
    def tracker(self) -> YaTracker:
        """Get Tracker client."""
        from yatracker.tracker import YaTracker

        return YaTracker.get_current()


class Printable:
    display: str | None

    def __str__(self) -> str:
        """Return display name."""
        try:
            return self.display or self.__class__.__name__
        except AttributeError:
            return super().__str__()
