from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from .base import BaseObject

if TYPE_CHECKING:
    from collections.abc import Iterator


class Issue(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    key: str
    display: str


class User(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    display: str


class Sprint(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    display: str


class IssueType(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    key: str
    display: str


class Priority(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    """Represents Priority.

    Attributes
    ----------
    url - Reference to the object.
    id - Priority ID.
    key - Priority key.
    version - Priority version.
    name - Display name of the priority. When localized=false is passed
    in the request, this parameter contains duplicates of
    the names in other languages.
    order - The weight of the priority. This parameter affects the order
    for displaying the priority in the interface.
    """

    url: str = msgspec.field(name="self")
    id: str
    key: str
    display: str | None = None
    version: int | None = None
    name: str | dict | None = None
    order: int | None = None


class Queue(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    key: str
    display: str


class Status(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    key: str
    display: str


class Transition(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    id: str = msgspec.field(name="self")
    url: str
    display: str
    to: Status

    async def execute(self) -> None:
        await self.tracker.execute_transition(self)


class Transitions(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.current = -1

    def __iter__(self) -> Iterator[Transition]:
        return self

    def __next__(self):
        self.current += 1
        values = list(self.values())
        if self.current >= len(values):
            raise StopIteration
        return values[self.current]


class Comment(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    text: str
    created_by: User
    updated_by: User | None = None
    created_at: str
    updated_at: str | None = None
    version: int
