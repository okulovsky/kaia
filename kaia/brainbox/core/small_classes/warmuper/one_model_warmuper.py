from typing import *
from ..installer import IInstaller

class OneModelWarmuper:
    def __init__(self,
                 installer_get_running_model: Optional[Callable[[IInstaller], Any]] = None,
                 installer_set_running_model_name: Optional[Callable[[IInstaller, str], None]] = None,
                 model_to_name: Optional[Callable[[Any], str]] = None,
                 ):
        self.installer_get_running_model = installer_get_running_model if installer_get_running_model is not None else self._default_get
        self.installer_set_running_model = installer_set_running_model_name if installer_set_running_model_name is not None else self._default_set
        self.model_to_name = model_to_name if model_to_name is not None else self._default_model_to_name


    def _default_get(self, installer: IInstaller):
        return installer.create_api().get_loaded_model()

    def _default_set(self, installer: IInstaller, model_name: str):
        installer.create_api().load_model(model_name)

    def _default_model_to_name(self, model: Any):
        return model['name']


    def load_model(self, installer: IInstaller, due_name: str|None):
        running_model = self.installer_get_running_model(installer)
        running_name = None if running_model is None else self.model_to_name(running_model)
        if due_name is None:
            if running_model is None:
                raise ValueError("There is no running model that could be default, also no model is provided in parameters")
            else:
                return
        else:
            if running_name is not None and running_name == due_name:
                return
            self.installer_set_running_model(installer, due_name)
            loaded_model = self.installer_get_running_model(installer)
            if loaded_model is None:
                raise ValueError(f"Failed warmup: ordered to load {due_name}, but nothing was loaded")
            loaded_name = self.model_to_name(loaded_model)
            if loaded_name != due_name:
                raise ValueError(f"Failed warmup: ordered to load {due_name}, but actually {loaded_name} was loaded")
            return

    def check_and_return_running_model(self, installer: IInstaller, due_name: str|None) -> Any:
        running_model = self.installer_get_running_model(installer)
        running_name = None if running_model is None else self.model_to_name(running_model)
        if running_name is None:
            raise ValueError("No model was loaded during warmup")
        if due_name is None:
            return running_model
        if running_name!=due_name:
            raise ValueError(f"Wrong model was loaded during warmup: {running_model} instead of {due_name}")
        return running_model



