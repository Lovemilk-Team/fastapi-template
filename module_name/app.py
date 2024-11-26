from os import PathLike
from pathlib import Path
from importlib import import_module
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .log import logger
from .shared import config
from .middlewares.rate_limiter import add_rate_limit
from .cn_cdn_docs_ui import replace_swagger_ui
from .fastapi_logger import replace_uvicorn_logger
from .handles.exception_handles import add_http_exception_handler, add_server_exception_handler, \
    add_request_validation_exception_handler, add_exception_handler_middleware

current_dir = Path(__file__).absolute().resolve().parent


def _path2import_path(relative_path: Path) -> str:
    """
    convert relative path to Python relative import path format

    TIP:
    filename or directory name which includes `.` is not supported because of Python import path format
    """
    _path = '.'.join(part if part != '..' else '.' for part in relative_path.parts)
    return '.' + _path if not _path.startswith('..') else _path


def _load_routers(target_dir: str | PathLike, target_router: APIRouter, *, ignore_py_special: bool = False):
    target_dir = Path(target_dir)

    for _file in target_dir.iterdir():  # 仅遍历顶层
        if not _file.is_file():
            continue

        if not _file.suffix.lower().endswith('.py'):
            continue

        if ignore_py_special and _file.stem.startswith('__') and _file.stem.endswith('__'):
            continue

        if '.' in _file.stem:
            logger.warning(
                'invalid py file name `{}` because `.` is in the file stem, skip to import',
                _file.name
            )
            continue

        # use `Path.with_suffix('')` to remove suffix
        _module_name = _path2import_path(_file.with_suffix('').relative_to(current_dir))
        _module = import_module(_module_name, current_dir.name)
        _router = getattr(_module, ROUTER_KEYNAME, None)
        if not isinstance(_router, APIRouter):
            del _module, _module_name, _router
            continue

        target_router.include_router(_router)
        logger.success('router `{}:{}` added', _module_name, ROUTER_KEYNAME)
        del _module, _module_name, _router


ROUTER_KEYNAME = 'router'
ROUTER_ROOT_PATH = ''  # root

replace_swagger_ui()
replace_uvicorn_logger(logger)
app = FastAPI(**config.app.model_dump())
app.add_middleware(
    CORSMiddleware,  # type: ignore
    **config.cors.model_dump()
)

if config.service.rate_limit.enable:
    add_rate_limit(app)
add_http_exception_handler(app)
add_server_exception_handler(app)
add_request_validation_exception_handler(app)
add_exception_handler_middleware(app)
root_router = APIRouter(prefix=ROUTER_ROOT_PATH)

logger.info('start to load routers...')
_load_routers(current_dir / 'routers/', root_router)
logger.success('routers are loaded')
if config.app.test_mode:
    logger.debug('test mode is enabled, loading test routers...')
    _load_routers(current_dir / 'tests/', root_router)
    logger.debug('test routers are loaded')
app.include_router(root_router)

from .commit_hash import COMMIT_HASH

logger.success('app startup completed, current commit hash `{}`', COMMIT_HASH)


@app.get('/')
async def index():
    current_file_url = Path(__file__).absolute().resolve().as_uri()

    return HTMLResponse(f'''
    <h1>Hello World!</h1>
    <p>if you can see this page, it means your server is working now!</p>
    <p>click <a href="https://github.com/Lovemilk-Team/fastapi-template/blob/main/module_name/config.py">here</a> to see the tutorial</p>
    <p>notes: your can find this HTML in the function `index` of `<a href="{current_file_url}" _target="_blank">app.py</a>`</p>
    '''.strip())
