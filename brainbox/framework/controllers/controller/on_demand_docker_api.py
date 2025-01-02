from ....framework import IDecider
from typing import Generic, TypeVar

TSettings = TypeVar('TSettings')
TController = TypeVar('TController')

class OnDemandDockerApi(IDecider, Generic[TSettings, TController]):
    @property
    def controller(self) -> TController:
        return self._controller

    @controller.setter
    def controller(self, controller: TController):
        self._controller = controller