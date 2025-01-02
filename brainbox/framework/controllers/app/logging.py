import copy

from ...deployment import LocalExecutor, IExecutor, Command, IFileSystem, Machine
from ...common import Logger
from dataclasses import dataclass
from datetime import datetime



class Log:
    @dataclass
    class Item:
        timestamp: datetime
        comment: str
        command: Command|None
        result: str|None

    def __init__(self):
        self.items: list['Log.Item'] = []


class LogLogger(Logger):
    def __init__(self, log: Log):
        self._log = log

    def report_progress(self, progress: float):
        self.log(f"Progress report: {100*progress}%")

    def log(self, s):
        self._log.items.append(Log.Item(
            datetime.now(),
            s,
            None,
            None
        ))





class LoggingLocalExecutor(IExecutor):
    def __init__(self, log: Log):
        self.base_executor = LocalExecutor()
        self.log = log

    def execute_command(self, command: Command):
        log_item = Log.Item(
            datetime.now(),
            None,
            command,
            None
        )
        command = copy.deepcopy(command)
        if command.options is None:
            command.options = Command.Options()
        command.options.return_output = True
        result = self.base_executor.execute_command(command)
        log_item.result = result
        self.log.items.append(log_item)
        return result

    def get_fs(self) -> IFileSystem:
        return self.base_executor.get_fs()

    def get_machine(self) -> Machine:
        return self.base_executor.get_machine()
