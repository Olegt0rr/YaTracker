from msgspec import Struct


class BaseObject(Struct, kw_only=True, omit_defaults=True, rename="camel"):
    @property
    def tracker(self):
        from yatracker.tracker import YaTracker

        return YaTracker.get_current()
