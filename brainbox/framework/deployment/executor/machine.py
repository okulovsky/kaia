import subprocess
from dataclasses import dataclass
from pathlib import Path
import os

class LocalMachine:
    _local = None

    @staticmethod
    def get():
        if LocalMachine._local is not None:
            return LocalMachine._local

        if os.name=='nt':
            user_id = 1000
            group_id = 1000
        else:
            user_id = int(subprocess.check_output(['id', '-u']).decode('ascii').strip())
            group_id = int(subprocess.check_output(['id', '-g']).decode('ascii').strip())
        LocalMachine._local = Machine(user_id, group_id, '127.0.0.1', '')
        return LocalMachine._local


@dataclass
class Machine:
    user_id: int
    group_id: int
    ip_address: str
    username: str


    @staticmethod
    def local():
        return LocalMachine.get()
