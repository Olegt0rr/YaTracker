from __future__ import annotations

__all__ = ["Duration"]

import re
from dataclasses import dataclass, fields

PATTERN = re.compile(
    r"^P(?=\d+[YMWD])"
    r"((?P<years>\d+)Y)?"
    r"((?P<months>\d+)M)?"
    r"((?P<weeks>\d+)W)?"
    r"((?P<days>\d+)D)?"
    r"(?P<time>T(?=\d+[HMS])"
    r"((?P<hours>\d+)H)?"
    r"((?P<minutes>\d+)M)?"
    r"((?P<seconds>\d+)S)?)?$",
)


@dataclass
class Duration:
    years: int = 0
    months: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

    def to_iso(self) -> str:
        """Convert Duration object to ISO data."""
        time = ""
        if self.hours:
            time = f"{time}{self.hours}H"
        if self.minutes:
            time = f"{time}{self.minutes}M"
        if self.seconds:
            time = f"{time}{self.seconds}S"

        duration = "P"
        if self.years:
            duration = f"{duration}{self.years}Y"
        if self.months:
            duration = f"{duration}{self.months}M"
        if self.days:
            duration = f"{duration}{self.days}D"
        if time:
            duration = f"{duration}T{time}"

        return duration

    @classmethod
    def from_iso(cls, duration: str, pattern: re.Pattern = PATTERN) -> Duration:
        """Create Duration object from ISO data."""
        result = pattern.match(duration)
        if result is None:
            msg = "Duration is not matched to ISO duration pattern."
            raise ValueError(msg)

        data: dict[str, int] = {}
        for field in fields(Duration):
            if value := result.group(field.name):
                data[field.name] = int(value)

        return cls(**data)
