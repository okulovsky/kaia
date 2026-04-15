from ..logging import Logger
from typing import TypeVar
from loguru import logger as loguru_logger

TResult = TypeVar('TResult')

def _on_item(item):
    for line in item.to_string().split('\n'):
        loguru_logger.info(line)

logger = Logger()
logger.ON_ITEM.append(_on_item)

