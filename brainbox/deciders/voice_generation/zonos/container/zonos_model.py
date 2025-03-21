import torch
import torchaudio
from zonos.model import Zonos
from zonos.conditioning import make_cond_dict

class ZonosModel:
    def __init__(self):
        self.model = Zonos.from_pretrained("Zyphra/Zonos-v0.1-transformer", device="cuda")

    def train(self, path_to_file):
        wav, sampling_rate = torchaudio.load(path_to_file)
        speaker = self.model.make_speaker_embedding(wav, sampling_rate)
        return speaker

    def voiceover(self, text, speaker_model, language, output_file, emotion, speaking_rate: int|float|None):
        if speaking_rate is None:
            speaking_rate = 15 #Default from gradio
        args = dict(
            text=text,
            speaker=speaker_model,
            language=language,
            speaking_rate = float(speaking_rate)
        )
        if emotion is not None:
            args['emotion'] = emotion
        cond_dict = make_cond_dict(**args)
        conditioning = self.model.prepare_conditioning(cond_dict)
        codes = self.model.generate(conditioning)
        wavs = self.model.autoencoder.decode(codes).cpu()
        torchaudio.save(output_file, wavs[0], self.model.autoencoder.sampling_rate)
