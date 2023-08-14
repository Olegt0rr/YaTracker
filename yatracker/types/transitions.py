from __future__ import annotations

__all__ = ["Transitions"]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .transition import Transition


class Transitions(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current = -1

    def __iter__(self) -> Iterator[Transition]:
        """Iterate via transitions."""
        return self

    def __next__(self) -> Transition:
        """Get next transition."""
        self.current += 1
        values = list(self.values())
        if self.current >= len(values):
            raise StopIteration
        return values[self.current]
