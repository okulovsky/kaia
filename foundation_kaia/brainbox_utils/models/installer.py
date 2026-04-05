from typing import Generic, TypeVar, Any
from pathlib import Path
from ...marshalling_2 import TypeTools, DeclaredType
import yaml
from dataclasses import dataclass
from typing import Any

TModelSpec = TypeVar('TModelSpec')

@dataclass
class LoadedModel(Generic[TModelSpec]):
    name: str | None
    spec: TModelSpec | None
    model: Any




class Installer(Generic[TModelSpec]):
    def __init__(self, resources_folder: Path|str = '/resources'):
        self.resources_folder = Path(resources_folder)

    @property
    def installation_file(self) -> Path:
        return self.resources_folder/'installation.yaml'

    def is_installed(self) -> bool:
        return self.installation_file.is_file()

    def _read_installation_file(self) -> dict[str, Any]:
        if not self.is_installed():
            raise ValueError("The service was not installed, path: "+str(self.installation_file))
        with open(self.installation_file, 'r') as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}
        return data

    def _read_model_spec_raw(self, model: str) -> Any:
        data = self._read_installation_file()
        if model not in data:
            return None
        return data[model]

    def is_model_installed(self, model: str) -> bool:
        return self._read_model_spec_raw(model) is not None

    def get_model_spec(self, model: str) -> TModelSpec:
        data = self._read_model_spec_raw(model)
        if data is None:
            raise ValueError(f"Model {model} is not isntalled")
        type = DeclaredType.parse(self).find_type(Installer).type_map[TModelSpec]
        spec = TypeTools.deserialize(data, type)
        return spec

    def _execute_unique_model_loading(self):
        raise NotImplementedError()

    def _execute_model_loading(self, model: str, model_spec: TModelSpec):
        raise NotImplementedError()

    def load_model(self, model: str|None) -> LoadedModel[TModelSpec]:
        if model is None:
            return LoadedModel(None, None, self._execute_unique_model_loading())
        else:
            spec = self.get_model_spec(model)
            return LoadedModel(model, spec, self._execute_model_loading(model, spec))

    def _execute_model_downloading(self, model: str, model_spec: TModelSpec):
        raise NotImplementedError()

    def _execute_installation(self):
        pass

    def download_model(self, model: str, model_spec: TModelSpec):
        self._execute_model_downloading(model, model_spec)
        installed = self._read_installation_file()
        installed[model] = TypeTools.serialize(model_spec, model_spec)
        with open(self.installation_file, 'w') as f:
            yaml.safe_dump(installed, f)

    def install_service(self):
        if not self.is_installed():
            self._execute_installation()
            with open(self.installation_file, 'w') as f:
                pass