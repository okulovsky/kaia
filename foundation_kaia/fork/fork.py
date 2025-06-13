import threading
import subprocess
import sys
import pickle
import atexit
import time
from uuid import uuid4
from typing import Callable
from ..misc import Loc


class Fork:
    def __init__(self, method: Callable, raise_if_exited: bool = True):
        self.method = method
        self.process: subprocess.Popen|None = None
        self.monitor_thread = None
        self.exception_raised = False
        self.raise_if_exited = raise_if_exited

    def start(self):
        try:
            path = Loc.temp_folder / ('fork_' + str(uuid4()))
            with open(path, 'wb') as stream:
                pickle.dump(self.method, stream)
        except Exception as ex:
            raise ValueError(f"Cannot pickle {self.method} to run in fork") from ex
        self.process = subprocess.Popen(
            [
                sys.executable,
                '-m',
                'foundation_kaia.fork.fork_worker',
                str(self.method),
                str(path)
            ],
        )
        atexit.register(self.terminate)

        if self.raise_if_exited:
            self.monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            self.monitor_thread.start()

        return self

    def _monitor_process(self):
        while True:
            if self.process.poll() is not None:
                if not self.exception_raised:
                    raise RuntimeError(f"Subprocess for {str(self.method)} exited unexpectedly with code {self.process.returncode}")
                break
            time.sleep(0.1)

    def terminate(self):
        if self.process and self.process.poll() is None:
            self.exception_raised = True
            self.process.terminate()
            self.process.wait()