import contextvars
from typing import Type, TypeVar

T = TypeVar("T")


class ContextInstanceMixin:
    def __init_subclass__(cls, **kwargs):
        cls.__context_instance = contextvars.ContextVar(f"instance_{cls.__name__}")
        return cls

    @classmethod
    def get_current(cls: Type[T], no_error=True) -> T:
        if no_error:
            return cls.__context_instance.get(None)  # type: ignore
        return cls.__context_instance.get()  # type: ignore

    @classmethod
    def set_current(cls: Type[T], value: T):
        if not isinstance(value, cls):
            raise TypeError(
                f"Value should be instance of {cls.__name__!r}, "
                f"not {type(value).__name__!r}"
            )
        cls.__context_instance.set(value)  # type: ignore
