from __future__ import annotations

__all__ = ["Base", "field"]

from msgspec import Struct, field

from .mixins import Printable, TrackerAccess


class Base(
    Printable,
    TrackerAccess,
    Struct,
    frozen=True,
    omit_defaults=True,
    rename="camel",
):
    """Base structure class."""
