from ..log import logger

__all__ = (
    'db_logger',
)

db_logger = logger.bind(name='database')
