from pydantic import BaseModel
from typing import Any, Mapping
from fastapi.routing import JSONResponse

__all__ = (
    'BaseResponse',
)


class BaseResponse(BaseModel):
    code: int
    message: str | None = None
    data: Any | None = None
    headers: Mapping[str, Any] | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.message is None:
            self.message = 'success' if 200 <= self.code <= 299 else 'error'

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.code,
            content=self.model_dump(mode='json'),
            headers=self.headers,
            media_type=JSONResponse.media_type
        )
