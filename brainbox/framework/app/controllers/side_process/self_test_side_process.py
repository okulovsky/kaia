from foundation_kaia.logging import Logger, ILogItem, logger
from .side_process_pool import ISideProcess
from pathlib import Path
from ....controllers import IController



class SelfTestSideProcess(ISideProcess):
    def __init__(self, controller: IController, self_test_folder:Path, api):
        self.controller = controller
        self.self_test_folder = self_test_folder
        self.api = api
        self._log = []

    def run(self):
        callback = None
        try:
            def on_item(e):
                self._log.append(e)
            callback = on_item
            Logger.ON_ITEM.append(callback)
            self.controller.self_test(self_test_folder=self.self_test_folder, api=self.api)
        except Exception as exception:
            logger.error(exception)
        finally:
            if callback is not None and callback in Logger.ON_ITEM:
                Logger.ON_ITEM.remove(callback)

    def get_report(self) -> list[ILogItem]:
        return self._log

