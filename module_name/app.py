from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .log import logger
from .shared import config
from .rate_limiter import add_rate_limit
from .cn_cdn_docs_ui import replace_swagger_ui
from .fastapi_logger import replace_uvicorn_logger
from .handles.exception_handles import add_http_exception_handler, add_exception_handler_middleware
from .handles.response_handles import add_response_middleware

replace_swagger_ui()
replace_uvicorn_logger(logger)
app = FastAPI(**config.app.model_dump())
app.add_middleware(
    CORSMiddleware,  # type: ignore
    **config.cors.model_dump()
)

add_rate_limit(app)
add_http_exception_handler()
add_exception_handler_middleware(app)
add_response_middleware(app)


@app.get('/')
async def index():
    return HTMLResponse('''
    <h1>Hello World!</h1>
    <p>if you can see this page, it means your server is working now!</p>
    <p>click <a href="https://github.com/Lovemilk-Team/fastapi-template/blob/main/module_name/config.py">here</a> to see the tutorial</p>
    '''.strip())
