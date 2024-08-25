from . import Command
from .executor import IExecutor
import subprocess
import os
from pathlib import Path
import shutil
from .machine import Machine
from kaia.infra import Loc

class LocalExecutor(IExecutor):
    def __init__(self, print_all: bool = False):
        self.print_all = print_all

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
                raise ValueError(f"Error launching subprocess with parameters\n{str_cmd}") from ex
            if result!=0:
                raise ValueError(f'Error running subprocess, arguments:\n{str_cmd}')
            return None

        try:
            output = subprocess.check_output(command.command, **kw, stderr=subprocess.STDOUT)
            return output
        except subprocess.CalledProcessError as exc:
            o_str = self._to_str(exc.output)
            raise ValueError(f'Error running subprocess, arguments:\n{str_cmd}\n\noutput:\n{o_str}')



    def upload_file(self, local_path: Path, remote_path: str):
        os.makedirs(Path(remote_path).parent, exist_ok=True)
        shutil.copy(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: Path):
        shutil.copy(remote_path, local_path)

    def create_empty_folder(self, path: str|Path):
        os.makedirs(path, exist_ok=True)

    def is_file(self, remote_path: str):
        return Path(remote_path).is_file()

    def is_dir(self, remote_path: str):
        return Path(remote_path).is_dir()

    def delete_file_or_folder(self, remote_path: str):
        if self.is_file(remote_path):
            os.unlink(remote_path)
        elif self.is_dir(remote_path):
            shutil.rmtree(remote_path)

    def get_machine(self):
        vram = os.environ.get('VRAM', None)
        if vram is not None:
            vram = int(vram)

        return Machine(
            Loc.is_windows,
            Loc.host_user_group_id,
            Loc.host_user_group_id,
            vram,
            Loc.data_folder,
            '127.0.0.1',
            Loc.username
        )
