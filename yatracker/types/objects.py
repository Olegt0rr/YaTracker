from pydantic import BaseModel


class Issue(BaseModel):
    link: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }


class User(BaseModel):
    link: str
    id: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }


class Sprint(BaseModel):
    link: str
    id: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }


class IssueType(BaseModel):
    link: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }


class Priority(BaseModel):
    link: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }


class Queue(BaseModel):
    link: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }


class Status(BaseModel):
    link: str
    id: str
    key: str
    display: str

    class Config:
        fields = {
            'link': {'alias': '_self'},
        }
