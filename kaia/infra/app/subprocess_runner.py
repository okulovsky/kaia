from typing import *
import time

from .runner import IRunner
import subprocess
from ..comm import Sql
from ..loc import Loc
import sys


def get_filename():
    return Loc.temp_folder/'subprocesses'



class SubprocessRunner(IRunner):
    def __init__(self, entry):
        self.entry = entry
        self.process = None #type: Optional[subprocess.Popen]
        self.wait_for_run_in_seconds = 10
        self.wait_for_exit_in_seconds = 2
        self.process_id = None #type: Optional[str]

    def run(self):
        messenger = Sql.file(get_filename()).messenger()
        self.process_id = messenger.add(self.entry, 'up')
        self.process = subprocess.Popen(
            [sys.executable, '-m', 'kaia.infra.app.subprocess_app', self.process_id],
        )
        for _ in range(self.wait_for_run_in_seconds*10):
            msg = messenger.Query(self.process_id).query_single(messenger)
            if msg.open:
                time.sleep(0.1)
                continue
            if msg.result is None:
                return
            raise ValueError(f'Entry {self.entry} failed:\n{msg.result}')
        raise ValueError(f'Failed to start entry {self.entry}')

    def stop(self):
        if self.process is None:
            return
        if self.process.returncode is not None:
            return
        if self.process is not None:
            messenger = Sql.file(get_filename()).messenger()
            id = messenger.add(None,'down',self.process_id)
            for _ in range(self.wait_for_exit_in_seconds * 10):
                time.sleep(0.1)
                msg = messenger.Query(id).query_single(messenger)
                if not msg.open:
                    self.process.terminate()
                    return
            self.process.terminate()
            raise ValueError(f'Cannot terminate process {self.entry} gracefully')



