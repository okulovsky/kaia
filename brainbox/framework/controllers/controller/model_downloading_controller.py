from typing import *
from abc import ABC, abstractmethod
from pathlib import Path
from .controller import IController

class DownloadableModel(ABC):
    @classmethod
    def from_dict(cls, dictionary: dict) -> Any:
        return None

    @abstractmethod
    def get_local_location(self, controller: IController) -> Path:
        pass

    @classmethod
    @abstractmethod
    def download(cls, models: list['DownloadableModel'], controller: IController):
        pass



class IModelDownloadingController:
    @abstractmethod
    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        pass


    def _ensure_type(self, model, index=None) -> DownloadableModel:
        _type = self.get_downloadable_model_type()
        if isinstance(model, _type):
            return model
        if isinstance(model, dict):
            value = _type.from_dict(model)
            if value is not None:
                return value
            try:
                return _type(**model)
            except:
                raise ValueError(f"Cannot resolve {_type} from arguments {model}")
        if index is None:
            index = ''
        else:
            index = f'(at index {index})'
        raise ValueError(f"Model {index} is expected to be dict or {_type}, but was neither")


    def _normalize_model_array(self, models: Any) -> List[DownloadableModel]:
        _type = self.get_downloadable_model_type()
        if isinstance(models, dict):
            return [self._ensure_type(models)]
        elif isinstance(models, _type):
            return [models]
        try:
            models = list(models)
        except:
            raise ValueError(f"Models has to be dict, {_type} or list of those two, but wasn't")
        result = []
        for index, model in enumerate(models):
            result.append(self._ensure_type(model, index))
        return result


    def download_models(self, models: Any):
        controller = cast(IController,self)
        models = self._normalize_model_array(models)
        models_to_download = []
        for model in models:
            controller.context.logger.log(f"Checking model {model}")
            location = model.get_local_location(self)
            if location.is_dir() or location.is_file():
                controller.context.logger.log("Model is already downloaded")
                continue
            controller.context.logger.log("Model needs to be downloaded")
            models_to_download.append(model)
        if len(models_to_download) == 0:
            controller.context.logger.log("All models are downloaded")
        else:
            controller.context.logger.log(f"Downloading {len(models_to_download)} models")
            _type = self.get_downloadable_model_type()
            _type.download(models_to_download, self)








