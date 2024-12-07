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
    def warmup(self, parameters: str|None):
        pass

    @abstractmethod
    def cooldown(self, parameters: str|None):
        pass

    @abstractmethod
    def create_brainbox_decider_api(self, parameters: str|None) -> IApiDecider:
        pass

    @abstractmethod
    def _brainbox_self_test_internal(self, api, tc: TestCase) -> Iterable[IntegrationTestResult]:
        pass


    @property
    def python_name(self):
        return type(self).__name__.replace('Installer','')


    def brainbox_self_test(self, tc: None|TestCase = None) -> tuple[IntegrationTestResult,...]:
        from ...core import BrainBoxTestApi
        from ...deciders.collector import Collector
        if tc is None:
            tc = TestCase()
        decider_name = type(self).__name__.replace('Installer','')
        try:
            with BrainBoxTestApi({decider_name:self, 'Collector':Collector()}) as api:
                return tuple(self._brainbox_self_test_internal(api, tc))
        finally:
            self.cooldown(None)

    def reinstall(self, purge: bool = False):
        if self.is_installed():
            self.uninstall(purge)
        self.install()
