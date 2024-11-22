from functools import partial
from asyncio import iscoroutine
from fastapi import FastAPI, Request
from fastapi.responses import Response
from typing import Any, Callable, TypeVar, Coroutine, Awaitable, TypeAlias
from fastapi.exceptions import HTTPException, StarletteHTTPException, RequestValidationError

from ..log import logger
from ..structs.responses import BaseResponse, ErrorResponse

__all__ = (
    'add_http_exception_handler',
    'add_exception_handler_middleware',
    'add_server_exception_handler',
    'add_request_validation_exception_handler'
)

_ExceptionType = TypeVar("_ExceptionType", bound=type[Exception])
_ExceptionHandlerType: TypeAlias = Callable[
    [Request, _ExceptionType],
    None | BaseResponse | Response | Awaitable[BaseResponse | Response] | Coroutine[Any, Any, BaseResponse | Response]
]
_exception_handlers: dict[
    _ExceptionType, list[_ExceptionHandlerType]
] = {}


def _get_handlers(exc: _ExceptionType) -> list[_ExceptionHandlerType] | None:
    return _exception_handlers[exc]


async def _exception_handler_middleware(handle_all: bool, request: Request, call_next):
    errored = True

    try:
        resp = await call_next(request)
        errored = False
        return resp
    except tuple(_exception_handlers.keys()) as exc:  # 相对引入和绝对引入的 Exception 不相等, 请注意!
        handlers = _get_handlers(type(exc))
        if not handlers:
            raise

        for handler in handlers:
            result = handler(request, exc)
            if iscoroutine(result):
                result = await result

            if isinstance(result, (Response, BaseResponse)):
                errored = False
                return result

        logger.exception(exc)
        raise
    except Exception as exc:
        logger.exception(exc)
        raise
    finally:
        if handle_all and errored:
            return BaseResponse(code=500)


def _add_handler(exc: _ExceptionType, handler: _ExceptionHandlerType):
    if exc not in _exception_handlers:
        _exception_handlers[exc] = []

    _exception_handlers[exc].append(handler)


# 由于 app.exception_handler 无法捕获位于 middleware 的 exception, 此处使用 middleware 实现
def add_http_exception_handler(app: FastAPI):
    async def _handle_http_exception(_: Request, exc: StarletteHTTPException) -> BaseResponse:
        return BaseResponse(code=exc.status_code, message=exc.detail, headers=exc.headers)

    _add_handler(HTTPException, _handle_http_exception)  # type: ignore
    _add_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore
    app.exception_handler(StarletteHTTPException)(_handle_http_exception)  # 处理由 fastapi 内部产生的 HTTPException


def add_server_exception_handler(app: FastAPI):
    """
    处理 ServerException
    handle ServerException
    `..structs.exceptions.ServerException`

    注意: 相对引入和绝对引入的 Exception 不相等, 请使用相对导入 (以 `.` 开头) 的 ServerException
    WARN: Please use the relative import (which starts with `.`) instead absolute import for ServerException
    because the exception in relative import and absolute import are not `==`.
    """
    from ..structs.exceptions import ServerException

    async def _handle_server_exception(_: Request, exc: ServerException) -> BaseResponse:
        return exc.response

    _add_handler(StarletteHTTPException, _handle_server_exception)  # type: ignore
    app.exception_handler(ServerException)(_handle_server_exception)


def add_request_validation_exception_handler(app: FastAPI):
    def _handle_request_validation_exception(_: Request, exc: RequestValidationError) -> ErrorResponse:
        return ErrorResponse(code=422, errors=exc.errors())

    app.exception_handler(RequestValidationError)(_handle_request_validation_exception)


def add_exception_handler_middleware(app: FastAPI, handle_all: bool = True):
    """
    add the middleware which can handle exceptions happened if you added it

    :param app: the FastAPI instance
    :param handle_all: if return a response with status code 500 even the exception happened you haven't added
    """
    app.middleware('http')(partial(_exception_handler_middleware, handle_all))
