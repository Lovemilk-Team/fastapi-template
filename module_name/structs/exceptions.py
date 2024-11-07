from typing import Any, Mapping

from .responses import BaseResponse

__all__ = (
    'ServerException',
)


class ServerException(Exception):
    def __init__(
            self, code: int, message: str | None = None, data: Any = None, headers: Mapping[str, Any] | None = None
    ) -> None:
        self._response = BaseResponse(code=code, message=message, data=data, headers=headers)

    def to_response(self):
        return self._response.to_response()
