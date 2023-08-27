from __future__ import annotations


class Printable:
    display: str | None

    def __str__(self) -> str:
        """Return display name."""
        try:
            return self.display or self.__class__.__name__
        except AttributeError:
            return super().__str__()
