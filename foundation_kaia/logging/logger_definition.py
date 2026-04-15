from .logger_class import Logger
from .log_item import ILogItem

def _on_log(item: ILogItem):
    print(item.to_string())

logger = Logger()