import sys
from loguru import logger

from .shared import config

logger.remove()

log_config_dict = config.log.model_dump()
stderr_kwargs = {k[7:]: v for k, v in log_config_dict.items() if k.startswith('stderr_')}
if not stderr_kwargs['format']:
    stderr_kwargs.pop('format')

logger.add(sys.stderr, backtrace=False, **stderr_kwargs)

file_kwargs = {k[5:]: v for k, v in log_config_dict.items() if k.startswith('file_')}
if not file_kwargs['format']:
    file_kwargs.pop('format')

logger.add(
    'logs/{time:YYYY-MM-DD}.log',
    diagnose=True,
    backtrace=True,
    encoding='u8',
    **file_kwargs
)
