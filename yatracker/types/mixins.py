from __future__ import annotations


class Printable:
    __slots__ = ()

    def __str__(self) -> str:
        """Return display name."""
        if "display" in getattr(type(self), "model_fields", {}):
            display = getattr(self, "display", None)
            return display or self.__class__.__name__
        return super().__str__()
