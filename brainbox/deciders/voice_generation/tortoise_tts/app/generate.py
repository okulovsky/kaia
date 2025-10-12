import os

from tortoise.utils.audio import load_voices
from torchaudio import save
from uuid import uuid4
from tortoise.utils.wav2vec_alignment import Wav2VecAlignment
import torch
from uuid import uuid4

def report_file_structure():
    lines = []
    for root, dirs, files in os.walk('/home/app'):
        for file in files:
            lines.append(os.path.join(root, file))
    raise ValueError("\n".join(lines))

class Generator:
    def __init__(self, tts):
        self.tts = tts
    def _generate(self, text, voice, count):
        voice_sel = [voice]
        voice_samples, conditioning_latents = load_voices(voice_sel)

        gen, dbg_state = self.tts.tts_with_preset(
            text,
            k=count,
            voice_samples=voice_samples,
            conditioning_latents=conditioning_latents,
            preset='fast',
            use_deterministic_seed=None,
            return_deterministic_state=True,
            cvvp_amount=0
        )

        if not isinstance(gen, list):
            gen = [gen]
        return gen


    def simple(self, text, voice, count):
        print(f'Voiceover simple, text `{text}` with voice `{voice}`')
        gen = self._generate(text, voice, count)
        print('Generated. Saving...')
        fnames = []
        for index, g in enumerate(gen):
            fname = f'{uuid4()}.output.{index}.wav'
            save(f'/stash/{fname}', g.squeeze(0).cpu(), 24000)
            fnames.append(fname)
        return fnames

#    This methiod allows you to get the part of audio for each token in the input
#    It's not very precise as sounds gradually transform into each other
#    Also, there is no real use case right now
#    def alignment(self, output_file_name, text, voice, count):
#        print(f'Voiceover aligned, text `{text}` with voice `{voice}`')
#        alignment = Wav2VecAlignment()
#        gen = self._generate(text, voice, count)
#        print('Generated. Saving...')
#        fnames = []
#        for index, g in enumerate(gen):
#            fname = f"{output_file_name}.aligned.{index}.wav.bin"
#            alignments = alignment.align(g.squeeze(1), text, 24000)
#            data = dict(audio = g, alignment = alignments)
#            torch.save(data, f'/stash/{fname}')
#            fnames.append(fname)
#
#       return fnames