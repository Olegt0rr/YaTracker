from typing import Optional, Union

from pydantic import BaseModel


class Issue(BaseModel):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class User(BaseModel):
    url: str
    id: str
    display: str

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class Sprint(BaseModel):
    url: str
    id: str
    display: str

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class IssueType(BaseModel):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class Priority(BaseModel):
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
            'url': {'alias': '_self'},
        }


class Queue(BaseModel):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class Status(BaseModel):
    url: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class Transition(BaseModel):
    id: str
    url: str
    display: str
    to: Status

    class Config:
        fields = {
            'url': {'alias': '_self'},
        }


class Comment(BaseModel):
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
            'url': {'alias': '_self'},
            'updated_by': {'alias': 'updatedBy'},
            'created_at': {'alias': 'createdAt'},
            'created_by': {'alias': 'createdBy'},
            'updated_at': {'alias': 'updatedAt'},
        }
