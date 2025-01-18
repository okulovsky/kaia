import copy

from ...deployment import LocalExecutor, IExecutor, Command, IFileSystem, Machine
from ...common import Logger
from dataclasses import dataclass
from datetime import datetime
from enum import Enum



class Log:
    @dataclass
    class Item:
        timestamp: datetime
        data: str

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
        ))





class LoggingLocalExecutor(IExecutor):
    def __init__(self, log: Log):
        self.base_executor = LocalExecutor()
        self.log = log

    def add_item(self, s):
        print(s)
        self.log.items.append(Log.Item(datetime.now(), '< ' + str(s)))

    def execute_command(self, command: Command):
        self.log.items.append(Log.Item(
            datetime.now(),
            '> ' + ' '.join(command.command)
        ))
        command = copy.copy(command)
        if command.options is None:
            command.options = Command.Options()
        command.options.monitor_output = self.add_item

        result = self.base_executor.execute_command(command)
        return result

    def get_fs(self) -> IFileSystem:
        return self.base_executor.get_fs()

    def get_machine(self) -> Machine:
        return self.base_executor.get_machine()

