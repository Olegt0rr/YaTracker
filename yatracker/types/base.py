from __future__ import annotations

__all__ = ["Base", "field"]

from typing import Any

from msgspec import Struct, field

from .mixins import Printable


class Base(Printable, Struct, omit_defaults=True, rename="camel"):
    """Base structure class."""

    _tracker: Any = None  # this field will be filled after decoding
