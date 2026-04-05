from ...marshalling_2 import service, endpoint
from .storages import IModelStorage

@service
class IModelLoadingSupport:
    @endpoint(force_json_params=True)
    def load_model(self, model: str) -> None:
        ...


class ModelLoadingSupport(IModelLoadingSupport):
    def __init__(self, storage: IModelStorage):
        self.storage = storage

    def load_model(self, model: str) -> None:
        self.storage.get_model(model)