import hashlib
import os
from dataclasses import dataclass
from foundation_kaia.brainbox_utils import Installer, download_file


@dataclass
class NemotronModelSpec:
    url: str
    filename: str
    size: int
    sha256: str
    rnnt_right_context: int = 1


class NemotronInstaller(Installer[NemotronModelSpec]):
    def _execute_installation(self):
        pass

    def _model_path(self, model_spec: NemotronModelSpec):
        return self.resources_folder / 'models' / model_spec.filename

    def _execute_model_downloading(self, model: str, model_spec: NemotronModelSpec):
        path = self._model_path(model_spec)
        path.parent.mkdir(parents=True, exist_ok=True)
        download_file(model_spec.url, path)
        try:
            self._verify(path, model_spec)
        except Exception:
            os.unlink(path)
            raise

    @staticmethod
    def _verify(path, model_spec: NemotronModelSpec):
        size = os.path.getsize(path)
        if size != model_spec.size:
            raise ValueError(f"{path}: expected size {model_spec.size}, but was {size}")
        sha = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(1 << 20):
                sha.update(chunk)
        if sha.hexdigest() != model_spec.sha256:
            raise ValueError(f"{path}: SHA-256 mismatch")

    def _execute_model_loading(self, model: str, model_spec: NemotronModelSpec):
        from nemo_asr import NemoRecognizer
        return NemoRecognizer(str(self._model_path(model_spec)), model_spec.rnnt_right_context)
