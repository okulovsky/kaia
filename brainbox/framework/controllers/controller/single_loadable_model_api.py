from abc import ABC, abstractmethod

class ISingleLoadableModelApi(ABC):
    @abstractmethod
    def load_model(self, model_name: str):
        pass

    @abstractmethod
    def get_loaded_model_name(self) -> str|None:
        pass
