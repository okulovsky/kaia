import os
import time

from .checkers import IRestartChecker
from .controllers import IProcessController
from pathlib import Path
from datetime import datetime
import json
import threading
from copy import copy

class Rebooter:
    def __init__(self,
                 checker: IRestartChecker,
                 controller: IProcessController,
                 log_file: Path,
                 pause_between_next_run_in_seconds = 60,
                 pause_between_checks_in_seconds = 60,
                 ):
        self.checher = checker
        self.controller = controller
        self.log_file = log_file
        self.pause_between_next_run_in_seconds = pause_between_next_run_in_seconds
        self.pause_between_checks_in_seconds = pause_between_checks_in_seconds
        self.iteration = -1

    def _write_event(self, event, **kwargs):
        dct = copy(kwargs)
        dct['event'] = event
        dct['timestamp'] = str(datetime.now())
        dct['iteration'] = self.iteration
        os.makedirs(self.log_file.parent, exist_ok=True)
        if self.log_file is not None:
            with open(self.log_file, 'a') as file:
                file.write(json.dumps(dct)+'\n')
        output = json.dumps(dct)
        if len(output) < 1000:
            print(json.dumps(dct))

    def _terminate(self):
        if self.controller.has_exited():
            self._write_event('exited')
            self._write_event('log', output=self.controller.get_output())
        else:
            self.controller.terminate(self.thread)
            self._write_event('terminated')
            self._write_event('log', output=self.controller.get_output())


    def _make_iteration(self):
        self._write_event('booting')
        self.thread = threading.Thread(target=self.controller.start)
        self.thread.start()
        self._write_event('booted')
        self.checher.reset()
        while True:
            reboot = self.checher.should_restart()
            if reboot is None:
                self._write_event('ok')
            else:
                self._write_event('reboot_request', reason = reboot)
                self._terminate()
                time.sleep(self.pause_between_next_run_in_seconds)
                break
            time.sleep(self.pause_between_checks_in_seconds)

    def _aborted(self):
        self._write_event('aborting')
        self._terminate()
        self._write_event('aborted')

    def run(self):
        try:
            while True:
                self.iteration+=1
                self._make_iteration()
        except KeyboardInterrupt:
            self._aborted()
        except:
            raise