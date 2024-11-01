from typing import *
from abc import ABC, abstractmethod
from unittest import TestCase
from .decider import IApiDecider
from .integration_test_result import IntegrationTestResult


class IInstaller(ABC):
    @abstractmethod
    def install(self):
        pass

    @abstractmethod
    def uninstall(self, purge: bool = False):
        pass

    @abstractmethod
    def is_installed(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def kill(self):
        pass

    @abstractmethod
    def is_running(self) -> bool:
        pass

    @abstractmethod
    def wait_for_running(self):
        pass

    @abstractmethod
    def create_api(self):
        pass

    def warmup(self, parameters: str):
        self.run_if_not_running_and_wait()

    def cooldown(self, parameters: str):
        self.kill()

    def create_brainbox_decider_api(self, parameters: str) -> IApiDecider:
        return self.create_api()


    @abstractmethod
    def _brainbox_self_test_internal(self, api, tc: TestCase) -> Iterable[IntegrationTestResult]:
        pass

    def brainbox_self_test(self, tc: None|TestCase = None) -> tuple[IntegrationTestResult,...]:
        from ..api import BrainBoxTestApi
        from ...deciders.collector import Collector
        if tc is None:
            tc = TestCase()
        decider_name = type(self).__name__.replace('Installer','')
        try:
            with BrainBoxTestApi({decider_name:self, 'Collector':Collector()}) as api:
                return tuple(self._brainbox_self_test_internal(api, tc))
        finally:
            self.kill()

    def run_if_not_running_and_wait(self):
        if not self.is_running():
            self.run()
            self.wait_for_running()
        return self.create_api()

    def run_in_any_case_and_create_api(self):
        if not self.is_installed():
            self.install()
        self.run_if_not_running_and_wait()
        return self.create_api()

    def reinstall(self, purge: bool = False):
        if self.is_installed():
            self.uninstall(purge)
        self.install()

    @property
    def python_name(self):
        return type(self).__name__.replace('Installer','')

