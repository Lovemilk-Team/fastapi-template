from typing import Any, Mapping

from .responses import BaseResponse

__all__ = (
    'ServerException',
)


class ServerException(Exception):
    def __init__(
            self, code: int, message: str | None = None, data: Any | None = None, errors: Any | None = None,
            headers: Mapping[str, Any] | None = None
    ) -> None:
        self._response = BaseResponse(code=code, message=message, data=data, errors=errors, headers=headers)

    @property
    def response(self):
        return self._response
