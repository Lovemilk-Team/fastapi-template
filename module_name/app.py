from fastapi import FastAPI

from .log import logger
from .shared import config
from .cn_cdn_docs_ui import replace_swagger_ui
from .fastapi_logger import replace_uvicorn_logger

replace_swagger_ui()
replace_uvicorn_logger(logger)
app = FastAPI(**config.app.model_dump())
