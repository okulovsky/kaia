from .installer import Installer, TModelSpec, LoadedModel
from typing import Generic, Any
from abc import ABC, abstractmethod

class IModelStorage(ABC, Generic[TModelSpec]):
    @abstractmethod
    def get_model_data(self, model: str) -> LoadedModel[TModelSpec]:
        pass

    def get_model(self, model: str) -> Any:
        return self.get_model_data(model).model


class MultiModelStorage(IModelStorage[TModelSpec], Generic[TModelSpec]):
    def __init__(self, installer: Installer[TModelSpec], default_model: str|None = None):
        self.installer = installer
        self.models: dict[str, LoadedModel[TModelSpec]] = {}
        self.default_model = default_model
        if self.default_model is not None and self.installer.is_installed() and self.installer.is_model_installed(default_model):
            self.models[self.default_model] = self.installer.load_model(default_model)

    def get_model_data(self, model: str|None):
        if model is None:
            model = self.default_model
        if model in self.models:
            return self.models[model]
        else:
            self.models[model] = self.installer.load_model(model)


class SingleModelStorage(IModelStorage[TModelSpec], Generic[TModelSpec]):
    def __init__(self, installer: Installer[TModelSpec], default_model: str|None = None):
        self.installer = installer
        self.current_model: LoadedModel[TModelSpec]|None = None
        if default_model is not None and self.installer.is_installed() and self.installer.is_model_installed(default_model):
            self.current_model = self.installer.load_model(default_model)

    def get_model_data(self, model: str|None) -> LoadedModel[TModelSpec]:
        if model is not None:
            if self.current_model is not None and model == self.current_model.name:
                return self.current_model
            self.current_model = self.installer.load_model(model)
            return self.current_model
        else:
            if self.current_model is None:
                raise ValueError("Model was not pre-initialized and was not specifically requested by the call")
            return self.current_model

    def get_model(self, model: str|None) -> Any:
        return self.get_model_data(model).model


class UniqueModelStorage(Generic[TModelSpec]):
    def __init__(self, installer: Installer[TModelSpec]):
        self.installer = installer
        self.model: LoadedModel[TModelSpec]|None = None
        if self.installer.is_installed():
            self.current_model = self.installer.load_model(None)

    def get_model_data(self, model: str|None) -> LoadedModel[TModelSpec]:
        if model is not None:
            raise ValueError("Service uses the unique model")
        else:
            if self.model is None:
                self.model = self.installer.load_model(None)
            return self.model