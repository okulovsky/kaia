from foundation_kaia.brainbox_utils import Installer


class CosyVoiceInstaller(Installer[str]):
    def _execute_installation(self):
        from modelscope import snapshot_download as snapshot_download_modelscope
        snapshot_download_modelscope("pengzhendong/wetext")

    def _execute_model_downloading(self, model: str, model_spec: str):
        from huggingface_hub import snapshot_download
        snapshot_download(
            f'FunAudioLLM/{model_spec}',
            local_dir=str(self.resources_folder / 'pretrained_models' / model_spec)
        )

    def _execute_model_loading(self, model: str, model_spec: str):
        from cosyvoice.cli.cosyvoice import AutoModel
        return AutoModel(model_dir=str(self.resources_folder / 'pretrained_models' / model_spec))
