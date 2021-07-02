from pydantic import BaseModel


class BaseObject(BaseModel):
    @property
    def tracker(self):
        from ..tracker import YaTracker

        return YaTracker.get_current()
