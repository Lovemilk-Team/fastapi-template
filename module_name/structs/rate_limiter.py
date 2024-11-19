import sys
from typing import Any
from datetime import datetime
from pydantic import Field
from pydantic.dataclasses import dataclass

__all__ = (
    'MatchFields',
    'MatchMethod',
    'RequestState'
)

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    # 手动创建 StrEnum 类型
    class StrEnum(str, Enum):
        pass
    del Enum


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
