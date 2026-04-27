from foundation_kaia.brainbox_utils import Installer


class ChatterboxInstaller(Installer[str]):
    def _execute_installation(self):
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        ChatterboxMultilingualTTS.from_pretrained(device=device)

    def _execute_unique_model_loading(self):
        import torch
        from processing import Model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return Model(device=device)
