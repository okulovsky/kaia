from ..logging import Logger, ILogItem
from typing import TypeVar
from loguru import logger as loguru_logger



TResult = TypeVar('TResult')

def _on_item(item: ILogItem):
    for line in item.to_string().split('\n'):
        loguru_logger.info(line)

logger = Logger(_on_item)




