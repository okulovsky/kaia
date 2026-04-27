from foundation_kaia.brainbox_utils import Installer


class WhisperInstaller(Installer[str]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: str):
        import whisper
        whisper.load_model(model, download_root='/resources/')

    def _execute_model_loading(self, model: str, model_spec: str):
        import whisper
        return whisper.load_model(model, download_root='/resources/')
