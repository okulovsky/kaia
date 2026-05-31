from foundation_kaia.logging import Logger, ILogItem, logger

from ..logging import LoggingLocalExecutor, LoggingApiCallback
from .side_process_pool import ISideProcess


class InstallationSideProcess(ISideProcess):
    def __init__(self, controller):
        self.controller = controller
        self._log: list[ILogItem] = []

    def run(self):
        callback = None
        try:
            self.controller.context._executor = LoggingLocalExecutor()
            self.controller.context._api_callback = LoggingApiCallback()

            def on_item(item):
                self._log.append(item)

            callback = on_item
            Logger.ON_ITEM.append(on_item)
            self.controller.install()
        except Exception as exception:
            logger.error(exception)
        finally:
            if callback is not None and callback in Logger.ON_ITEM:
                Logger.ON_ITEM.remove(callback)

    def get_report(self) -> list[ILogItem]:
        return self._log

