import yaml
from pathlib import Path
from http import HTTPStatus
from functools import cached_property
from datetime import time, timedelta
from typing import Callable, Any, TypeVar, Iterable
from pydantic import BaseModel, model_validator, Field
from fastapi.openapi.models import License as AppLicense, Contact as AppContact

from .structs.rate_limiter import MatchFields, MatchMethod

try:
    # LibYAML is much faster
    from yaml import Cloader as Loader, CDumper as Dumper
except ImportError:
    # fallback: default implement based on Python
    from yaml import Loader, Dumper

APP_VERSION = '0.1.0'
MERGED_CONFIG_PATH = './merged.config.yml'


# NOTE: timedelta will be converted to https://en.wikipedia.org/wiki/ISO_8601 format by Pydantic.
# like 10 seconds is `PT10S`

class AppConfig(BaseModel):
    """
    see
    https://fastapi.tiangolo.com/zh/reference/fastapi/#fastapi.FastAPI
    and
    https://www.uvicorn.org/settings/
    """
    host: str = '127.0.0.1'
    port: int | str = 8000
    reload: bool = False
    proxy_headers: bool = True
    test_mode: bool = Field(
        default=False,
        description='use test mode, if it was True, the routers in `<module-name>/tests/` will be included to app'
    )

    title: str = 'Lovemilk FastAPI Template'
    summary: str | None = None
    description: str | None = None
    docs_url: str | None = '/docs'
    redoc_url: str | None = '/redoc'
    root_path: str | None = None
    contact: AppContact | None = None
    license_info: AppLicense | None = AppLicense(
        name='Lovemilk (c) 2024, All Rights Reserved', url='https://aka.lovemilk.top/68'
    )

    @cached_property
    def version(self) -> str:
        return APP_VERSION


class LogConfig(BaseModel):
    stderr_level: int | str = Field(default='DEBUG', description='the log level of stderr')
    stderr_format: str | None = Field(
        default=None, description='the log format of stderr (None to use default format by loguru)'
    )

    file_level: int | str = Field(default='INFO', description='the log level of log file')
    file_format: str | None = Field(
        default=None, description='the log format of log file (None to use default format by loguru)'
    )
    file_rotation: str | int | time | timedelta = Field(default='00:00', description='the log rotation of log file')
    file_retention: str | int | timedelta = Field(default='30 days', description='the log retention of log file')


class RateLimitConfig(BaseModel):
    enable: bool = Field(default=False, description='enable rate limit or not')
    window_time: timedelta | None = Field(
        default=None,
        description='the window time of rate limit (request will be counted which\'s '
                    'timestamp is less than window time)'
    )
    limit: int | None = Field(default=None, description='the max requests of each window time of rate limit')
    match_fields: MatchFields | list[MatchFields] | None = Field(
        default=None, description='which field(s) to check if is the same client of rate limit'
    )
    match_method: MatchMethod | None = Field(
        default=None,
        description='use `and` or `or` to check if is the same client of rate limit for each field'
    )

    status_code: int = Field(
        default=HTTPStatus.TOO_MANY_REQUESTS.value,
        description='the status code if rate limit exceeded'
    )
    message: str | list | dict | None = Field(
        default=None,
        description='the message if rate limit exceeded'
    )

    @model_validator(mode='after')
    def verify_fields(self):
        if not self.enable:
            return self

        ATTR_NAMES = ('window_time', 'limit', 'match_fields', 'match_method')
        for _attr in ATTR_NAMES:
            _attr_value = getattr(self, _attr)
            assert _attr_value is not None, f'`{_attr}` must be defined when enable is True'

        if not isinstance(self.match_fields, list):
            self.match_fields = [self.match_fields]

        if self.message is None:
            self.message = HTTPStatus(self.status_code).phrase

        return self


class DatabaseConfig(BaseModel):
    class Config:
        extra = 'allow'

    enable: bool = Field(default=False, description='enable database')
    url: str | None = Field(default=None, description='database url')
    extras: dict = Field(  # like **kwargs
        default_factory=dict, description='internal dict who receive the extra fields to SQLModel.create_engine'
    )

    @model_validator(mode='after')
    def verify_fields(self):
        if not self.enable:
            return self

        ATTR_NAMES = ('url', )
        for _attr in ATTR_NAMES:
            _attr_value = getattr(self, _attr)
            assert _attr_value is not None, f'`{_attr_value}` must be defined when enable is True'
        return self


class ServiceConfig(BaseModel):
    rate_limit: RateLimitConfig = RateLimitConfig()
    database: DatabaseConfig = DatabaseConfig()


class CORSConfig(BaseModel):
    """
    see
    https://fastapi.tiangolo.com/tutorial/cors/
    """
    allow_origins: list[str] = ['*']
    allow_methods: list[str] = ['*']
    allow_headers: list[str] = ['*']
    allow_credentials: bool = False
    allow_origin_regex: str | None = None
    expose_headers: list[str] = ['*']
    max_age: int = 600


class Config(BaseModel):
    app: AppConfig = AppConfig()
    log: LogConfig = LogConfig()
    service: ServiceConfig = ServiceConfig()
    cors: CORSConfig = CORSConfig()


def _load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists() or not path.is_file():
        return {}

    try:
        with path.open('r', encoding='u8') as fp:
            loaded = yaml.load(fp, Loader=Loader)
            return loaded if isinstance(loaded, dict) else {}
    except (FileNotFoundError, PermissionError):
        return {}


_ReturnType = TypeVar('_ReturnType')


def _map_files(
        filenames: str | Iterable[str | Path], suffixes: str | Iterable[str], callback: Callable[[Path], _ReturnType]
) -> list[_ReturnType]:
    result = []

    filenames = (filenames,) if isinstance(filenames, str) else filenames
    suffixes = (suffixes,) if isinstance(suffixes, str) else suffixes

    for filename in filenames:
        path = Path(filename + suffixes[0])  # 避免后缀被吞
        for suffix in suffixes:
            path_with_suffix = path.with_suffix(suffix)
            if not path_with_suffix.is_file():
                continue
            result.append(callback(path_with_suffix))

    return result


def create_config(config: Config, *, path: str | Path = MERGED_CONFIG_PATH, force_write: bool = True):
    """
    generate a complete merged configuration file
    NOTE:
    you can cp, edit and rename it to make your own config
    """
    path = Path(path)
    if not force_write and path.exists():
        return

    try:
        with path.open('w', encoding='u8') as fp:
            fp.write(yaml.dump(
                config.model_dump(mode='json'),
                default_flow_style=False,
                allow_unicode=True,
                Dumper=Dumper,
            ))
    except (FileExistsError, PermissionError):
        pass


def load_config() -> Config:
    from os import getenv
    _format_key: Callable[[str], str] = lambda key: key.strip().lower().replace('-', '_')

    _is_dev = getenv('MILK_DEVMODE', '').strip() == '1'
    config_dict: dict = {}
    for config in _map_files(
            ('config', 'prod.config') + ('dev.config',) if _is_dev else (),
            ('.json', '.yaml', '.yml'),
            _load_yaml
    ):
        # 统一化为小写的 key
        config_dict.update({_format_key(k): v for k, v in config.items()})

    config = Config(**config_dict)
    if not _is_dev:
        create_config(config)
    return config
