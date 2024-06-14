import os
from typing import *
from .executor import IExecutor, ExecuteOptions
from pathlib import Path
import subprocess
import shutil

class LocalExecutor(IExecutor):
    def _to_str(self, output):
        if isinstance(output, str):
            return output
        try:
            return output.decode('utf-8')
        except:
            return output


    def execute(self, command: str | Iterable[str], options: ExecuteOptions|None = None):
        if options is None:
            options = ExecuteOptions()

        kw = {}
        if options.workdir is not None:
            kw['cwd'] = str(options.workdir)
        str_cmd = self.argument_to_string(command)

        if not options.return_output:
            try:
                result = subprocess.call(command, **kw)
            except Exception as ex:
                raise ValueError(f"Error launching subprocess with parameters\n{command}") from ex

            if result!=0:
                raise ValueError(f'Error running subprocess, arguments:\n{str_cmd}')
            return None

        try:
            output = subprocess.check_output(command, **kw, stderr=subprocess.STDOUT)
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
