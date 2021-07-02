from typing import Iterator, Optional, Union

from .base import BaseObject


class Issue(BaseObject):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


class User(BaseObject):
    url: str
    id: str
    display: str

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


class Sprint(BaseObject):
    url: str
    id: str
    display: str

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


class IssueType(BaseObject):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


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

    url: str
    id: str
    key: str
    display: Optional[str]
    version: Optional[int]
    name: Optional[Union[str, dict]]
    order: Optional[int]

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


class Queue(BaseObject):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


class Status(BaseObject):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }


class Transition(BaseObject):
    id: str
    url: str
    display: str
    to: Status

    class Config:
        fields = {
            "url": {"alias": "_self"},
        }

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
    url: str
    id: str
    text: str
    created_by: User
    updated_by: User
    created_at: str
    updated_at: str
    version: int

    class Config:
        fields = {
            "url": {"alias": "_self"},
            "updated_by": {"alias": "updatedBy"},
            "created_at": {"alias": "createdAt"},
            "created_by": {"alias": "createdBy"},
            "updated_at": {"alias": "updatedAt"},
        }
