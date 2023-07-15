from typing import *
from ..infra.comm import IComm
from dataclasses import dataclass
from abc import ABC, abstractmethod
import multiprocessing
import atexit

@dataclass
class KaiaAppConfig:
    comm: IComm

class IKaiaService(ABC):
    @abstractmethod
    def run(self, app_config: KaiaAppConfig):
        pass


class KaiaApp:
    def __init__(self):
        self.services = [] #type: List[IKaiaService]
        self.primary_service = None #type: Optional[IKaiaService]
        self.processes = [] # type: List[multiprocessing.Process]

    def add_service(self, service: IKaiaService, primary = False):
        if not primary:
            self.services.append(service)
        else:
            if self.primary_service is None:
                self.primary_service = service
            else:
                raise ValueError('App already contains primary service')

    def exit(self):
        for process in self.processes:
            process.terminate()

    def run(self, config: KaiaAppConfig):
        for service in self.services:
            process = multiprocessing.Process(target = service.run, kwargs = dict(app_config = config))
            self.processes.append(process)
            process.start()
        atexit.register(self.exit)
        if self.primary_service is not None:
            self.primary_service.run(config)





