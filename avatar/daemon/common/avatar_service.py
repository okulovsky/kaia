from ...messaging import IService
from abc import ABC, abstractmethod

class AvatarService(IService, ABC):
    @abstractmethod
    def requires_brainbox(self):
        return True

