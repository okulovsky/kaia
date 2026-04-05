import copy
from brainbox.framework.common import ApiCallback
from brainbox.framework.deployment import LocalExecutor, IExecutor, Command, IFileSystem, Machine
from foundation_kaia.logging import logger


class LoggingLocalExecutor(IExecutor):
    def __init__(self):
        self._base = LocalExecutor()

    def execute_command(self, command: Command):
        logger.info('> ' + ' '.join(str(c) for c in command.command))
        command = copy.copy(command)
        if command.options is None:
            command.options = Command.Options()
        original_monitor = command.options.monitor_output
        def monitor(s):
            logger.info('< ' + str(s))
            if original_monitor is not None:
                original_monitor(s)
        command.options.monitor_output = monitor
        return self._base.execute_command(command)

    def get_fs(self) -> IFileSystem:
        return self._base.get_fs()

    def get_machine(self) -> Machine:
        return self._base.get_machine()


class LoggingApiCallback(ApiCallback):
    def report_progress(self, progress: float):
        logger.info(f"Progress: {100 * progress:.0f}%")

    def log(self, s):
        logger.info(s)
