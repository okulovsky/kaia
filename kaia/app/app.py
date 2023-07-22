from typing import *
from ..infra.comm import IComm
from dataclasses import dataclass
from abc import ABC, abstractmethod
import multiprocessing
import atexit


class KaiaApp:
    def __init__(self):
        self.services = [] #type: List[Callable]
        self.primary_service = None #type: Optional[Callable]
        self.processes = [] # type: List[multiprocessing.Process]

    def add_service(self, service: Callable, primary = False):
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

    def run(self):
        for service in self.services:
            process = multiprocessing.Process(target = service)
            self.processes.append(process)
            process.start()
        atexit.register(self.exit)
        if self.primary_service is not None:
            self.primary_service()





