from typing import *
from pathlib import Path
from .decomposer import Decomposer
from ....brainbox import MediaLibrary
from ..core import Utterance, Template
from ....eaglesong.core import Audio
from kaia.infra import Loc, FileIO
from uuid import uuid4
import os
import subprocess
from unittest import TestCase

class Dubber:
    def __init__(self,
                 vocabulary: Dict[str, Dict[str, Path]],
                 ):
        self.vocabulary = vocabulary
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

    def decompose_string(self, s, template):
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
            files.extend(self.decompose_string(s, u.template))
        return files, ' '.join(strings)

    def dub(self, utterances: Union[Utterance, Iterable[Utterance]]):
        files, _ = self.decompose(utterances)
        return self.create_wav_file(files)

    def dub_to_audio(self, utterances: Union[Utterance, Iterable[Utterance]]):
        files, s = self.decompose(utterances)
        with Loc.create_temp_file('dubber', 'wav') as output_path:
            self.create_wav_file(files, output_path)
            with open(output_path, 'rb') as stream:
                data = stream.read()
        return Audio(data, s)


    @staticmethod
    def concat_audio_with_ffmpeg(paths: Iterable[Path], output_path:Path):
        control_content_array = [f"file '{p}'" for p in paths]
        control_content = '\n'.join(control_content_array)
        with Loc.create_temp_file('dubber', 'txt', True) as control_path:
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


    def create_wav_file(self, decomposition: List[str], output_path: Optional[Path] = None) -> Path:
        paths = []
        uuid = str(uuid4())
        for file in decomposition:
            paths.append(file)
            if self.silence is not None:
                paths.append(self.create_silence_file_if_needed(self.silence))

        if output_path is None:
            output_path = self.output_folder / (uuid + ".wav")

        Dubber.concat_audio_with_ffmpeg(paths, output_path)

        return output_path

    @staticmethod
    def from_media_library(
            library: MediaLibrary,
            voice: Optional[str] = None,
            option_index: int = 0):
        if voice is None:
            voice = library.records[0].tags['voice']
        voc = {}
        for record in library.records:
            if record.tags['voice'] != voice or record.tags['option_index'] != option_index:
                continue
            dub = record.tags['dub']
            if dub not in voc:
                voc[dub] = {}
            voc[dub][record.tags['text']] = record.get_full_path()
        return Dubber(voc)


    def fake_decompose_and_check(self,
                                 test: TestCase,
                                 s: str,
                                 template: Template,
                                 voice: Optional[str] = None
                                 ):
        dec = self.decompose_string(s, template)
        files = [FileIO.read_json(d) for d in dec]
        built = ''.join(f['text'] for f in files)
        built = built.lower().replace(' ', '').replace('.','').replace(',', '')
        s = s.lower().replace(' ', '').replace('.', '').replace(',', '')
        test.assertEqual(s, built)
        if voice is not None:
            test.assertTrue(all(f['voice']==voice for f in files))
