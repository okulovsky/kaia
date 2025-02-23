import torch
import torchaudio
from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from zonos.utils import DEFAULT_DEVICE as device

class Model:
    def __init__(self):
        self.model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device=device)

    def compute_embedding(self, src_path):
        wav, sampling_rate = torchaudio.load(src_path)
        speaker = self.model.make_speaker_embedding(wav, sampling_rate)
        return speaker

    def voiceover(self, text, speaker, language, output_file):
        print(text)
        print(language)
        print(output_file)
        cond_dict = make_cond_dict(text=text, speaker=speaker, language=language)
        conditioning = self.model.prepare_conditioning(cond_dict)
        codes = self.model.generate(conditioning)
        wavs = self.model.autoencoder.decode(codes).cpu()
        torchaudio.save(output_file, wavs[0], self.model.autoencoder.sampling_rate)