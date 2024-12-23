from . import Command
from .executor import IExecutor
import subprocess
from .file_system import IFileSystem
from .local_file_system import LocalFileSystem
from .machine import Machine

class LocalExecutor(IExecutor):
    def get_fs(self) -> IFileSystem:
        return LocalFileSystem()

    def get_machine(self) -> Machine:
        return Machine.local()

    def _to_str(self, output):
        if isinstance(output, str):
            return output
        try:
            return output.decode('utf-8')
        except:
            return output

    def execute_command(self, command: Command):
        kw = {}
        if command.options is not None and command.options.workdir is not None:
            kw['cwd'] = str(command.options.workdir)
        str_cmd = " ".join(command.command)
        print(str_cmd)

        if command.options is None or not command.options.return_output:
            try:
                result = subprocess.call(command.command, **kw)
            except Exception as ex:
                raise ValueError(f"Error launching subprocess, arguments:\n{str_cmd}") from ex
            if result!=0:
                if command.options is not None and command.options.ignore_exit_code:
                    pass
                else:
                    raise ValueError(f'Error running subprocess, arguments:\n{str_cmd}')
            return None

        try:
            output = subprocess.check_output(command.command, **kw, stderr=subprocess.STDOUT)
            return self._to_str(output)
        except subprocess.CalledProcessError as exc:
            o_str = self._to_str(exc.output)
            if command.options is not None and command.options.ignore_exit_code:
                pass
            else:
                raise ValueError(f'Error running subprocess, arguments:\n{str_cmd}\n\noutput:\n{o_str}')



