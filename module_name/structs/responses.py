from http import HTTPStatus
from typing import Any, Mapping
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

__all__ = (
    'BaseResponseModel',
    'BaseResponse',
    'basemodel2response'
)


def basemodel2response(status_code: int, model: BaseModel, *, headers=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=model.model_dump(mode='json'),
        headers=headers,
        media_type=JSONResponse.media_type
    )


class BaseResponseModel(BaseModel):
    code: int
    message: str | None = None
    data: Any | None = None
    errors: Any | None = None

    def model_post_init(self, __context: Any) -> None:
        self.message = HTTPStatus(self.code).phrase if self.message is None else self.message


class BaseResponse(JSONResponse):
    def __init__(
            self, code: int | BaseResponseModel, message: str | None = None, data: Any | None = None,
            errors: Any | None = None, **kwargs
    ):
        """
        create `BaseResponse`

        :param code: the status code of response if it's an int, or it must be a `BaseResponseModel` instance
        :param message: the message of response (`None` to use the default message of http status corresponded)
        :param data: the data of response or `None`
        :param errors: the errors of response or `None`
        """
        if isinstance(code, BaseResponseModel):
            _content = basemodel2response(code.code, code, **kwargs)
        else:
            self.code = code
            self.message = HTTPStatus(self.code).phrase if message is None else message
            self.data = data
            self.errors = errors

            _content = BaseResponseModel(
                code=self.code, message=self.message, data=self.data, errors=errors
            ).model_dump(mode='json')

        super().__init__(
            content=_content,
            status_code=self.code,
            media_type=JSONResponse.media_type,
            **kwargs
        )
