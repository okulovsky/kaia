import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

class Model:
    def __init__(self, device = 'cuda'):
        self.model = ChatterboxMultilingualTTS.from_pretrained(device=device)

    def compute_embedding(self, src_path):
        self.model.prepare_conditionals(src_path, exaggeration=0.5)
        return self.model
    
    def voiceover(self, text, speaker, language, output_file, exaggeration=0.5, cfg_weight=1):
        wav_out = speaker.generate(
            text=text,
            language_id=language,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight
        )
        torchaudio.save(output_file, wav_out, speaker.sr)