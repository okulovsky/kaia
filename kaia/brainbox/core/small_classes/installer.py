from abc import ABC, abstractmethod
from ....infra.deployment import IExecutor, LocalExecutor
from unittest import TestCase


class IInstaller(ABC):
    @property
    def executor(self) -> IExecutor:
        if not hasattr(self, '_executor'):
            self._executor = LocalExecutor()
        return self._executor

    @executor.setter
    def executor(self, value: IExecutor):
        self._executor = value

    @abstractmethod
    def is_installed(self) -> bool:
        pass

    @abstractmethod
    def install(self):
        pass

    @abstractmethod
    def uninstall(self):
        pass

    def self_test(self, tc: TestCase):
        pass

    def install_if_not_installed(self):
        if not self.is_installed():
            self.install()

    def reinstall(self):
        if self.is_installed():
            self.uninstall()
        self.install()


class IInstallable(ABC):
    @abstractmethod
    def get_installer(self) -> IInstaller:
        pass





