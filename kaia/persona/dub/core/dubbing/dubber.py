from typing import *
from pathlib import Path
from .decomposer import Decomposer
from ...core import Dub, Template, Utterance
from .....eaglesong.core import Audio
from kaia.infra import Loc, FileIO
from uuid import uuid4
import os
import subprocess

class Dubber:
    def __init__(self,
                 vocabulary: Dict[str, Dict[str, str]],
                 wav_folder: Path
                 ):
        self.vocabulary = vocabulary
        self.wav_folder = wav_folder
        self.output_folder = Loc.temp_folder/'dubs'
        self.silence = None #type: Optional[float]
        os.makedirs(self.output_folder, exist_ok=True)

    def create_silence_file_if_needed(self, silence: float) -> Path:
        silence = str(silence)
        path = Loc.temp_folder/f"silence{silence.replace('.','_')}.wav"
        if not path.is_file():
            subprocess.call([
                Loc.get_ffmpeg(),
                '-f',
                'lavfi',
                '-i',
                'anullsrc=r=11025:cl=mono',
                '-t',
                silence,
                path
            ])
        return path

    def _decompose(self, s, template):
        decomposition = Decomposer(s, self.vocabulary).walk(template.dub).to_list()
        if len(decomposition) == 0:
            raise ValueError(f'Cannot decompose string to template {template}. String is\n{s}')
        return decomposition[0]


    def decompose(self, utterances: Union[Utterance, Iterable[Utterance]]) -> Tuple[List[str], str]:
        if isinstance(utterances, Utterance):
            utterances = [utterances]
        files = []
        strings = []
        for u in utterances:
            s = u.to_str()
            strings.append(s)
            files.extend(self._decompose(s, u.template))
        return files, ' '.join(strings)

    def dub(self, utterances: Union[Utterance, Iterable[Utterance]]):
        files, _ = self.decompose(utterances)
        return self.create_wav_file(files)

    def dub_to_audio(self, utterances: Union[Utterance, Iterable[Utterance]]):
        files, s = self.decompose(utterances)
        with Loc.temp_file('dubber','wav') as output_path:
            self.create_wav_file(files, output_path)
            with open(output_path, 'rb') as stream:
                data = stream.read()
        return Audio(data, s)

    def create_wav_file(self, decomposition: List[str], output_path: Optional[Path] = None) -> Path:
        control_content_array = []
        uuid = str(uuid4())
        for file in decomposition:
            control_content_array.append(f"file '{self.wav_folder / file}'")
            if self.silence is not None:
                control_content_array.append(f"file '{self.create_silence_file_if_needed(self.silence)}'")
        control_content = '\n'.join(control_content_array)

        if output_path is None:
            output_path = self.output_folder / (uuid + ".wav")

        with Loc.temp_file('dubber', 'txt') as control_path:
            FileIO.write_text(control_content, control_path)

            args = [
                str(Loc.get_ffmpeg()),
                '-f',
                'concat',
                '-safe',
                '0',
                '-i',
                str(control_path),
                '-y',
                str(output_path)
            ]
            result = subprocess.call(args)
            if result != 0:
                raise ValueError(f'FFMpeg returned non-zero value. arguments are\n{" ".join(args)}')

        return output_path
