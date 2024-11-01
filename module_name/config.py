from pathlib import Path
from fastapi.openapi.models import License as AppLicense, Contact as AppContact
from typing import Callable, Any, TypeVar, Iterable
from pydantic import BaseModel, Field
from functools import cache, cached_property
from datetime import time, timedelta
import yaml

try:
    # 优先使用 LibYAML 速度更快
    from yaml import Cloader as Loader, CDumper as Dumper
except ImportError:
    # 回退到 Python 的普通实现
    from yaml import Loader, Dumper

APP_VERSION = '0.1.0'
RECOMMENDED_CONFIG_PATH = './config.yml'

@cache
def _get_module_name(current_file: str | Path) -> str:
    return Path(current_file).absolute().resolve().parent.name

class AppConfig(BaseModel):
    """
    FastAPI APP 配置
    https://fastapi.tiangolo.com/zh/reference/fastapi/#fastapi.FastAPI
    """
    host: str = '127.0.0.1'
    port: int | str = 8000
    reload: bool = False
    proxy_headers: bool = True

    module_name: str = Field(default_factory=lambda: _get_module_name(__file__))
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
    stderr_level: int | str = 'DEBUG'
    stderr_format: str | None = None

    file_level: int | str = 'INFO'
    file_format: str | None = None
    file_rotation: str | int | time | timedelta = '00:00'
    file_retention: str | int | timedelta = '30 days'


class Config(BaseModel):
    app: AppConfig = AppConfig()
    log: LogConfig = LogConfig()


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


def create_config(config: Config, *, path: str | Path = RECOMMENDED_CONFIG_PATH):
    """
    配置文件不存在时生成一个完整的默认配置
    """
    path = Path(path)
    if path.exists():
        return

    try:
        with path.open('w', encoding='u8') as fp:
            fp.write(yaml.dump(
                config.model_dump(mode='json'),
                default_flow_style=False,
                Dumper=Dumper
            ))
    except (FileExistsError, PermissionError):
        pass


def load_config() -> Config:
    _format_key: Callable[[str], str] = lambda key: key.strip().lower().replace('-', '_')

    config_dict: dict = {}
    for config in _map_files(
            ('config', 'prod.config', 'dev.config'),
            ('.json', '.yaml', '.yml'),
            _load_yaml
    ):
        # 统一化为小写的 key
        config_dict.update({_format_key(k): v for k, v in config.items()})

    config = Config(**config_dict)
    create_config(config)
    return config
