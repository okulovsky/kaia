from pathlib import Path
from foundation_kaia.brainbox_utils import Installer


class WhisperKenLMState:
    def __init__(self, processor, model):
        self.processor = processor
        self.model     = model
        self.lm        = None


class WhisperKenLMInstaller(Installer[str]):
    def _execute_installation(self):
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        WhisperProcessor.from_pretrained('openai/whisper-base')
        WhisperForConditionalGeneration.from_pretrained('openai/whisper-base')

    def _execute_unique_model_loading(self):
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        processor = WhisperProcessor.from_pretrained('openai/whisper-base')
        model     = WhisperForConditionalGeneration.from_pretrained('openai/whisper-base')
        state     = WhisperKenLMState(processor, model)
        binary    = Path('/resources/lm/lm.binary')
        if binary.exists():
            import kenlm
            state.lm = kenlm.Model(str(binary))
        return state
