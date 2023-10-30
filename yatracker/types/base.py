from __future__ import annotations

__all__ = ["Base", "field"]

from typing import Any

from msgspec import Struct, field

from .mixins import Printable


class Base(Printable, Struct, omit_defaults=True, rename="camel"):
    """Base structure class."""

    _tracker: Any = None  # this field will be filled after decoding

    def __repr__(self) -> str:
        """Represent the object without tech fields."""
        fields = ", ".join(
            [
                f"{k}={getattr(self, k)!r}"
                for k in self.__struct_fields__
                if not k.startswith("_")
            ],
        )
        return f"{self.__class__.__name__}({fields})"
