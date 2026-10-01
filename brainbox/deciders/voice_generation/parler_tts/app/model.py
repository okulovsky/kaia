import json
from pathlib import Path

from foundation_kaia.brainbox_utils import Installer


class ParlerTtsInstaller(Installer[str]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: str):
        from huggingface_hub import snapshot_download
        folder = Path(snapshot_download(model_spec))
        text_encoder = json.loads((folder / 'config.json').read_text()).get('text_encoder', {}).get('_name_or_path')
        if text_encoder is not None and text_encoder != model_spec:
            snapshot_download(
                text_encoder,
                allow_patterns=['*.json', '*.txt', '*.model', 'spiece.model', 'tokenizer*'],
            )

    def _execute_model_loading(self, model: str, model_spec: str):
        from processing import Model
        return Model(model_spec)
