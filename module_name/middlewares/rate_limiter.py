from fastapi import Request, FastAPI
from datetime import timedelta, datetime
from typing import Callable, Any, Sequence
from fastapi.exceptions import HTTPException

from ..log import logger
from ..shared import config
from ..structs.rate_limiter import MatchFields, MatchMethod, RequestState

__all__ = (
    'add_rate_limit'
)

_field_mapping: dict[MatchFields, Callable[[Request], Any]] = {
    MatchFields.IP.value: lambda _req: _req.client.host,
    MatchFields.USERAGENT.value: lambda _req: _req.headers.get('User-Agent'),
    MatchFields.COOKIE.value: lambda _req: _req.cookies,
    MatchFields.AUTH.value: lambda _req: _req.headers.get('Authorization'),
}

_match_fields: list[MatchFields] = config.service.rate_limit.match_fields
_match_method: MatchMethod = config.service.rate_limit.match_method
_window_time: timedelta = config.service.rate_limit.window_time
_limit: int = config.service.rate_limit.limit
_status_code: int = config.service.rate_limit.status_code
_message: str | None = config.service.rate_limit.message


def _map_seq(seq_1: Sequence[Any] | dict, seq_2: Sequence[Any] | dict, *, ignore_empty: bool):
    return ((ignore_empty and (not item or item not in seq_2)) or item == seq_2[key]
            for key, item in (seq_1.items() if isinstance(seq_1, dict) else enumerate(seq_1)))


def _and(seq_1: Sequence[Any] | dict, seq_2: Sequence[Any] | dict) -> bool:
    return all(_map_seq(seq_1, seq_2, ignore_empty=False))


def _or(seq_1: Sequence[Any] | dict, seq_2: Sequence[Any] | dict) -> bool:
    return any(_map_seq(seq_1, seq_2, ignore_empty=True))


def add_rate_limit(app: FastAPI):
    if not config.service.rate_limit.enable:
        raise RuntimeError('rate limit is not enabled')

    rate_limit_datas: list[RequestState] = []
    rate_limit_logger = logger.bind(name='rate_limiter')

    async def _remove_olds():
        nonlocal rate_limit_datas
        _now = datetime.utcnow()
        for index in range(len(rate_limit_datas) - 1, -1, -1):  # 从后开始找直到第一个超出 _window_time 的请求
            request_state = rate_limit_datas[index]
            if _now - request_state.timestamp > _window_time:
                rate_limit_datas = rate_limit_datas[index + 1:]  # 由于是顺序 appended, 所以可以直接删除前面的
                rate_limit_logger.debug('removed old requests by index from 0 to {}', index)
                break

    async def _rate_limit_middleware(request: Request, call_next):
        nonlocal rate_limit_datas
        await _remove_olds()  # 先移除掉超出 _window_time 的请求

        _fields = dict(  # 获取各字段
            filter(
                lambda _item: _item[1] is not None and _item[1] is not ...,
                {_field.value: _field_mapping[_field.value](request) for _field in _match_fields}.items()
            )
        )
        if _match_method.value == MatchMethod.OR.value:
            _last_requests = filter(lambda _item: _or(_fields, _item.fields), rate_limit_datas)
        elif _match_method.value == MatchMethod.AND.value:
            _last_requests = filter(lambda _item: _and(_fields, _item.fields), rate_limit_datas)
        else:
            rate_limit_logger.error('invalid match method `{}`', _match_method)
            assert False, f'invalid match method `{_match_method}`'

        _last_request_count = 0
        for _ in _last_requests:  # filter 不能用 len
            _last_request_count += 1

        rate_limit_datas.append(
            RequestState(fields=_fields)  # type: ignore
        )

        if _last_request_count > _limit:
            rate_limit_logger.error(
                'rate limit exceeded: requested {} times in {} is more than {} time limit,'
                ' status: {}, detail: {} (for client `{}`)',
                _last_request_count, _window_time, _limit, _status_code, _message, _fields
            )
            raise HTTPException(status_code=_status_code, detail=_message)
        return await call_next(request)

    app.middleware('http')(_rate_limit_middleware)
    rate_limit_logger.success('rate limiter enabled!')
