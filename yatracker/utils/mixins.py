import contextvars
from typing import TypeVar

T = TypeVar("T")


class ContextInstanceMixin:
    def __init_subclass__(cls, **kwargs):
        """Create context variable on subclass init."""
        cls.__context_instance = contextvars.ContextVar(f"instance_{cls.__name__}")
        return cls

    @classmethod
    def get_current(cls: type[T]) -> T:
        """Get current object from context."""
        return cls.__context_instance.get()

    @classmethod
    def set_current(cls: type[T], value: T) -> None:
        """Set current object for context."""
        if not isinstance(value, cls):
            msg = (
                f"Value should be instance of {cls.__name__!r}, not "
                f"{type(value).__name__!r}"
            )
            raise TypeError(msg)
        cls.__context_instance.set(value)
