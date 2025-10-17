import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

class Model:
    def __init__(self, device):
        self.model = ChatterboxMultilingualTTS.from_pretrained(device=device)

    def compute_embedding(self, src_path):
        self.model.prepare_conditionals(src_path, exaggeration=0.5)
