from http import HTTPStatus
from typing import Any, Mapping
from pydantic import BaseModel, Field
from fastapi.routing import JSONResponse

__all__ = (
    'BaseResponse',
)


class BaseResponse(BaseModel):
    code: int
    message: str | None = None
    data: Any | None = None
    headers: Mapping[str, Any] | None = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        if self.message is None:
            self.message = HTTPStatus(self.code).phrase

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.code,
            content=self.model_dump(mode='json'),
            headers=self.headers,
            media_type=JSONResponse.media_type
        )
