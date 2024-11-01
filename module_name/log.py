import sys
from loguru import logger

from .shared import config

logger.remove()
logger.add(sys.stderr, level=config.log.stderr_level, format=config.log.stderr_format, backtrace=False)
logger.add(
    'logs/{time:YYYY-MM-DD}.log',
    level=config.log.file_level,
    rotation='00:00',
    retention='30 days',
    diagnose=True,
    backtrace=True,
    format=config.log.file_format,
    encoding='u8',
)
