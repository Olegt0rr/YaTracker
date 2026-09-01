from __future__ import annotations

__all__ = ["Base", "field"]

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator
from pydantic.alias_generators import to_camel

from .mixins import Printable

if TYPE_CHECKING:
    from pydantic import ValidationInfo


def field(*args: Any, name: str | None = None, **kwargs: Any) -> Any:  # noqa: ANN401
    """Build a pydantic FieldInfo (thin wrapper around `pydantic.Field`).

    Accepts the legacy ``name=`` keyword (msgspec-era API) as an
    alias for pydantic's ``alias=``.
    """
    if name is not None:
        kwargs.setdefault("alias", name)
    return Field(*args, **kwargs)


class Base(Printable, BaseModel):
    """Base structure class."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
        coerce_numbers_to_str=True,
    )

    _tracker: Any = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _inject_tracker(self, info: ValidationInfo) -> Base:
        """Add the producer tracker object to the `_tracker` private field."""
        if info.context is not None:
            self._tracker = info.context.get("tracker")
        return self
