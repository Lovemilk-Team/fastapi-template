from sqlmodel import Session
from sqlalchemy import Select
from pydantic import BaseModel
from asyncio import iscoroutine
from fastapi.responses import Response
from typing import Sequence, Callable, Any
from fastapi.exceptions import HTTPException
from inspect import signature, Parameter, Signature

from ..database import dbsession_depend
from ..structs.responses import BaseResponse

__all__ = (
    'BasePage',
    'LimitOffsetPage',
    'use_limit_pagination'
)


def _get_merged_func_sign(
        *functions: Callable[..., Any],
        skip_VAR_POSITIONAL: bool = True,
        skip_VAR_KEYWORD: bool = True,
) -> tuple[Signature, dict[str, Any]]:
    _is_VAR_POSITIONAL: Callable[[Parameter], bool] = lambda param: param.kind == Parameter.VAR_POSITIONAL
    _is_VAR_KEYWORD: Callable[[Parameter], bool] = lambda param: param.kind == Parameter.VAR_KEYWORD

    params = []
    annotations = {}
    for sign in map(signature, functions):
        for param in sign.parameters.values():
            if skip_VAR_POSITIONAL and _is_VAR_POSITIONAL(param) or skip_VAR_KEYWORD and _is_VAR_KEYWORD(param):
                continue

            params.append(param)
            annotations[param.name] = param.annotation

    return Signature(params), annotations


def _merge_func_sign(func: Callable[..., Any], *functions: Callable[..., Any]):
    func.__signature__, func.__annotations__ = _get_merged_func_sign(*functions, func)


class InvalidParamError(ValueError):
    def __init__(self, msg: str, param: str):
        super().__init__(msg)
        self._msg = msg
        self._param = param

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def param(self) -> str:
        return self._param


class BasePage(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    statement: Sequence | Select

    def apply_pagination(self) -> Sequence | Select:
        raise NotImplementedError


class LimitOffsetPage(BasePage):
    statement: Select
    limit: int | None = None
    offset: int | None = None
    min_limit: int | None = 0
    max_limit: int | None = None

    def apply_pagination(self) -> Select:
        # check on runtime
        if self.min_limit is not None and self.limit is not None and self.limit < self.min_limit:
            raise InvalidParamError(
                f'invalid limit, expect `limit >= {self.min_limit}`, but got `{self.limit}`',
                param='limit'
            )

        if self.max_limit is not None and self.limit is not None and self.limit > self.max_limit:
            raise InvalidParamError(
                f'invalid limit, expect `limit <= {self.max_limit}`, but got `{self.limit}`',
                param='limit'
            )

        return self.statement.offset(self.offset).limit(self.limit)


def use_limit_pagination(
        func: Callable[..., LimitOffsetPage] | None = None,
        /, *,  # 拒绝 func 使用位置关键字传参, 并拒绝如下参数使用位置传参
        response_generator: Callable[[Sequence[Any]], Response] = lambda data: BaseResponse(
            code=200, data=data
        ),
        handle_select: bool = False,
        invalid_code: int = 422,
        invalid_message: str = 'invalid param `{param}`: {msg}'
):
    """
    use limit pagination (the pagination which based on limit and offset) for function return value

    :param func: _wrapper will be called automatically if it's function
    :param response_generator: a function which accept one position argument (the result) and will return a FastAPI Response instance
    :param handle_select: handle return value if it is select statement object or not
    :param invalid_code: the HTTP status code when an invalid parma provided
    :param invalid_message: the error message when an invalid parma provided (use `{param}` and `{msg} to stands for the name of param and the error message)

    TIP:
    `@use_limit_pagination` (without call) is equivalent to `@use_limit_pagination()` when no arguments are provided
    """

    def _wrapper(_func: Callable):
        async def _pagination_handler(
                limit: int | None = None,  # query
                offset: int | None = None,  # query
                session: Session = dbsession_depend,
                *args, **kwargs
        ) -> Response:
            response = _func(*args, **kwargs)
            if iscoroutine(response):
                response = await response

            if handle_select and isinstance(response, Select):
                response = LimitOffsetPage(statement=response)  # convert to LimitOffsetPage

            if not isinstance(response, LimitOffsetPage):
                return response

            response.limit = response.limit if response.limit is not None else limit
            response.offset = response.offset if response.offset is not None else offset
            try:
                handled_statement = response.apply_pagination()
            except InvalidParamError as exc:
                raise HTTPException(
                    status_code=invalid_code, detail=invalid_message.format(param=exc.param, msg=exc.msg)
                )

            return response_generator(session.exec(handled_statement).all())

        # 将形参(名称及其类型)和函数签名合并, 并忽略 `*args` 和 `**kwargs`
        _merge_func_sign(_pagination_handler, _func)
        return _pagination_handler

    return _wrapper(func) if isinstance(func, Callable) else _wrapper
