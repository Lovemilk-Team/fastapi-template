import sys
from typing import Any
from datetime import datetime
from pydantic import Field
from pydantic.dataclasses import dataclass

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum as StrEnum


class MatchFields(StrEnum):
    IP = 'ip'
    USERAGENT = 'useragent'
    COOKIE = 'cookies'
    AUTH = 'auth'


class MatchMethod(StrEnum):
    AND = 'and'
    OR = 'or'


@dataclass
class RequestState:
    fields: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
