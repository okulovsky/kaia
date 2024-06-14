from typing import *
from .loc import Loc
from pathlib import Path
import subprocess
import os
import stat
from abc import ABC, abstractmethod

class Executor(ABC):
    @abstractmethod
    def execute(self, cmd: Union[str, Iterable[str]], workdir: Union[None, str, Path] = None):
        pass

    def argument_to_string(self, cmd: Union[str, Iterable[str]]) -> str:
        if isinstance(cmd, str):
            return cmd
        return ' '.join(cmd)


class WindowsDemoExecutor(Executor):
    def __init__(self, wait):
        self.wait = wait

    def execute(self, cmd: Union[str, Iterable[str]], workdir: Union[None, str, Path] = None):
        with Loc.create_temp_file('executor','bat') as bat_location:
            with open(bat_location, 'w') as file:
                file.write(self.argument_to_string(cmd))
                if self.wait:
                    file.write('\npause')
            kw = {}
            if workdir is not None:
                kw['cwd'] = str(workdir)
            subprocess.call([bat_location], creationflags=subprocess.CREATE_NEW_CONSOLE, **kw)


class LinuxDemoExecutor(Executor):
    def __init__(self, wait):
        self.wait = wait

    def execute(self, cmd: Union[str, Iterable[str]], workdir: Union[None, str, Path] = None):
        with Loc.create_temp_file('executor', 'sh') as sh_location:
            with open(sh_location, 'w') as file:
                file.write(self.argument_to_string(cmd))
                if self.wait:
                    file.write('\necho Press ENTER to close')
                    file.write('\nread')
            os.chmod(sh_location, 0o777)
            if workdir is not None:
                os.chdir(workdir)
            os.system(f"gnome-terminal --wait -- bash -c '{sh_location}; exit'")


class SilentExecutor(Executor):
    def execute(self, cmd: Union[str, Iterable[str]], workdir: Union[None, str, Path] = None):
        kw = {}
        if workdir is not None:
            kw['cwd'] = str(workdir)
        result = subprocess.call(cmd, **kw)
        if result!=0:
            str_cmd = cmd
            if not isinstance(str_cmd, str):
                str_cmd = ' '.join(str_cmd)
            raise ValueError(f'Error running subprocess, arguments:\n{str_cmd}')


class ConsoleExecutor:
    wait = False
    @staticmethod
    def execute(cmd, folder = None):
        if Loc.is_windows:
            WindowsDemoExecutor(ConsoleExecutor.wait).execute(cmd, folder)
        else:
            LinuxDemoExecutor(ConsoleExecutor.wait).execute(cmd, folder)


