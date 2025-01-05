from . import Command
from .executor import IExecutor
import subprocess
from .file_system import IFileSystem
from .local_file_system import LocalFileSystem
from .machine import Machine
from .local_executor_scenarios import ExecutionScenario

class LocalExecutor(IExecutor):
    def get_fs(self) -> IFileSystem:
        return LocalFileSystem()

    def get_machine(self) -> Machine:
        return Machine.local()



    def execute_command(self, command: Command):
        kw = {}
        if command.options is not None and command.options.workdir is not None:
            kw['cwd'] = str(command.options.workdir)
        str_cmd = " ".join(command.command)
        scenatio = ExecutionScenario(
            command.command,
            command.options if command.options is not None else Command.Options(),
            str_cmd,
            kw
        )
        return scenatio.execute()

