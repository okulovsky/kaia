from typing import *
from .runner import IRunner
from .multiprocess_runner import MultiprocessingRunner
from .subprocess_runner import SubprocessRunner
import atexit
import time



class KaiaApp:
    def __init__(self):
        self.services = [] #type: List[IRunner]
        self.primary_service = KaiaApp.run_forever #type: Optional[Callable]

    def add_runner(self, runner: IRunner):
        self.services.append(runner)

    def add_multiproc_service(self, service: Callable[[],Any]):
        self.services.append(MultiprocessingRunner(service))

    def add_subproc_service(self, service: Callable[[], Any]):
        self.services.append(SubprocessRunner(service))

    def set_primary_service(self, service: Callable[[], Any]):
        self.primary_service = service

    def exit(self):
        for runner in self.services:
            runner.stop()

    def run(self):
        self.run_services_only()
        self.primary_service()
        self.exit()

    def run_services_only(self):
        atexit.register(self.exit)
        for runner in self.services:
            runner.run()

    @staticmethod
    def run_forever():
        while True:
            time.sleep(1)


    def test_runner(self):
        return KaiaAppTestRunner(self)


class KaiaAppTestRunner:
    def __init__(self, app: KaiaApp):
        self.app = app

    def __enter__(self):
        self.app.run_services_only()


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app.exit()


