from typing import *
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import os
import requests


class IRestartChecker(ABC):
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def should_restart(self) -> Optional[str]:
        pass


class FileRestartChecker(IRestartChecker):
    def __init__(self,
                 file_to_monitor: Path,
                 allowed_pause_in_seconds: int
                 ):
        self._file_to_monitor = file_to_monitor
        self.allowed_pause_in_seconds = allowed_pause_in_seconds

    @property
    def file_to_monitor(self):
        return self._file_to_monitor

    def reset(self):
        self.restart_time = datetime.now()

    def should_restart(self) -> Optional[str]:
        now = datetime.now()

        stat = os.stat(self.file_to_monitor)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        if (now - self.restart_time).total_seconds() < self.allowed_pause_in_seconds:
            return None
        if (now - last_modified).total_seconds() > self.allowed_pause_in_seconds:
            return 'file_not_updated'
        return None


class WebServerAvailabilityChecker(IRestartChecker):
    def __init__(self,
                 url_to_monitor,
                 expected_response
                 ):
        self.url_to_monitor = url_to_monitor
        self.expected_response = expected_response

    def reset(self):
        pass

    def should_restart(self) -> Optional[str]:
        try:
            response = requests.get(self.url_to_monitor)
            if response.status_code != 200:
                return f'status code {response.status_code}'
            if self.expected_response is None:
                return None
            if self.expected_response != response.text:
                return f'wrong response {response.text}'
            return None
        except:
            return f'cannot connect'
