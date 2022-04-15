from typing import Iterator, Optional, Union

from pydantic import Field

from .base import BaseObject


class Issue(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    key: str
    display: str


class User(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    display: str


class Sprint(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    display: str


class IssueType(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    key: str
    display: str


class Priority(BaseObject):
    """
    Attributes:
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

    url: str = Field(..., alias="_self")
    id: str
    key: str
    display: Optional[str]
    version: Optional[int]
    name: Optional[Union[str, dict]]
    order: Optional[int]


class Queue(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    key: str
    display: str


class Status(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    key: str
    display: str


class Transition(BaseObject):
    id: str = Field(..., alias="_self")
    url: str
    display: str
    to: Status

    async def execute(self):
        await self.tracker.execute_transition(self)


class Transitions(dict):
    def __init__(self, *args, **kwargs):
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


class Comment(BaseObject):
    url: str = Field(..., alias="_self")
    id: str
    text: str
    created_by: User = Field(..., alias="createdBy")
    updated_by: User = Field(..., alias="updatedBy")
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")
    version: int
