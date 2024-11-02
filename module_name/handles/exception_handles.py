from asyncio import iscoroutine
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.exceptions import StarletteHTTPException
from typing import Any, Callable, TypeVar, Coroutine, Awaitable, TypeAlias

from ..structs.responses import BaseResponse

__all__ = (
    'add_http_exception_handler',
    'add_exception_handler_middleware'
)

_ExceptionType = TypeVar("_ExceptionType", bound=type[Exception])
_ExceptionHandlerType: TypeAlias = Callable[
    [Request, _ExceptionType],
    None | BaseResponse | Response | Awaitable[BaseResponse | Response] | Coroutine[Any, Any, BaseResponse | Response]
]
_exception_handlers: dict[
    _ExceptionType, list[_ExceptionHandlerType]
] = {}


def _get_handler(exc: _ExceptionType) -> list[_ExceptionHandlerType] | None:
    for exc_type, handler in _exception_handlers.items():
        if issubclass(exc, exc_type):  # type: ignore
            return handler


async def _exception_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except tuple(_exception_handlers.keys()) as exc:
        handlers = _get_handler(type(exc))
        if not handlers:
            raise

        for handler in handlers:
            result = handler(request, exc)
            if iscoroutine(result):
                result = await result

            if isinstance(result, BaseResponse):
                return result.to_response()
            elif isinstance(result, Request):
                return result

        raise


def _add_handler(exc: _ExceptionType, handler: _ExceptionHandlerType):
    if exc not in _exception_handlers:
        _exception_handlers[exc] = []

    _exception_handlers[exc].append(handler)


def add_http_exception_handler():
    # 由于 app.exception_handler 无法捕获位于 middleware 的 exception, 此处使用 middleware 实现
    async def _handle_http_exception(_: Request, exc: StarletteHTTPException):
        return BaseResponse(code=exc.status_code, message=exc.detail, headers=exc.headers)

    _add_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore


def add_exception_handler_middleware(app: FastAPI):
    app.middleware('http')(_exception_handler_middleware)
