import subprocess
import sys
from typing import *
from uuid import uuid4
from .loc import Loc
import pickle
import atexit
from pathlib import Path

class Fork:
    def __init__(self, method: Callable):
        self.path = Loc.temp_folder/('fork_'+str(uuid4()))
        with open(self.path, 'wb') as stream:
            pickle.dump(method, stream)

    def start(self):
        self.process = subprocess.Popen([
            sys.executable,
            '-m',
            'brainbox.framework.common.fork_worker',
            str(self.path)
        ])
        atexit.register(self.terminate)
        return self

    def terminate(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait()









