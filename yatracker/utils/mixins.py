import contextvars
from typing import TypeVar

T = TypeVar("T")


class ContextInstanceMixin:
    def __init_subclass__(cls, **kwargs):
        cls.__context_instance = contextvars.ContextVar(f"instance_{cls.__name__}")
        return cls

    @classmethod
    def get_current(cls: type[T], no_error=True) -> T:
        if no_error:
            return cls.__context_instance.get(None)
        return cls.__context_instance.get()

    @classmethod
    def set_current(cls: type[T], value: T) -> None:
        if not isinstance(value, cls):
            msg = (
                f"Value should be instance of {cls.__name__!r}, not "
                f"{type(value).__name__!r}"
            )
            raise TypeError(msg)
        cls.__context_instance.set(value)
