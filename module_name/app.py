from pathlib import Path
from importlib import import_module
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .log import logger
from .shared import config
from .rate_limiter import add_rate_limit
from .cn_cdn_docs_ui import replace_swagger_ui
from .fastapi_logger import replace_uvicorn_logger
from .handles.exception_handles import add_http_exception_handler, add_server_exception_handler, \
    add_exception_handler_middleware
from .handles.response_handles import add_response_middleware

ROUTER_KEYNAME = 'router'
ROUTER_ROOT_PATH = ''  # root

replace_swagger_ui()
replace_uvicorn_logger(logger)
app = FastAPI(**config.app.model_dump())
app.add_middleware(
    CORSMiddleware,  # type: ignore
    **config.cors.model_dump()
)

add_rate_limit(app)
add_http_exception_handler(app)
add_server_exception_handler(app)
add_exception_handler_middleware(app)
add_response_middleware(app)

root_router = APIRouter(prefix=ROUTER_ROOT_PATH)

_current_dir = Path(__file__).absolute().resolve().parent
for _file in (_current_dir / 'routers').iterdir():  # 仅遍历顶层
    if not _file.is_file():
        continue

    if not _file.suffix.lower().endswith('.py'):
        continue

    _module_name = f'.routers.{_file.stem}'
    _module = import_module(_module_name, _current_dir.name)
    _router = getattr(_module, ROUTER_KEYNAME, None)
    if not isinstance(_router, APIRouter):
        del _module, _module_name, _router
        continue

    root_router.include_router(_router)
    logger.success('router `{}:{}` added!', _module_name, ROUTER_KEYNAME)
    del _module, _module_name, _router
del _current_dir

app.include_router(root_router)


@app.get('/')
async def index():
    return HTMLResponse('''
    <h1>Hello World!</h1>
    <p>if you can see this page, it means your server is working now!</p>
    <p>click <a href="https://github.com/Lovemilk-Team/fastapi-template/blob/main/module_name/config.py">here</a> to see the tutorial</p>
    '''.strip())
