import dataclasses
import datetime
import os
from typing import *
from abc import ABC, abstractmethod
from ...eaglesong.core import Audio
from ...brainbox import BrainBoxTaskPack, BrainBoxWebApi, BrainBoxTask, DownloadingPostprocessor
from ..dub.core import Utterance
from ...infra import Loc, FileIO
from ...infra.ffmpeg import FFmpegTools
from uuid import uuid4


class IDubbingService(ABC):
    @abstractmethod
    def dub_string(self, s: str, voice: str) -> Audio:
        pass

    def dub_utterance(self, utterance: Utterance, voice: str) -> Audio:
        return self.dub_string(utterance.to_str(), voice)

    def _iterate_mixed_arguments(self, lines: Union[str, Utterance, Iterable[Union[str,Utterance]]]) -> Union[str, Utterance]:
        if isinstance(lines, str) or isinstance(lines, Utterance):
            lines = [lines]
        else:
            lines = list(lines)
        for i, line in enumerate(lines):
            if isinstance(line, str) or isinstance(line, Utterance):
                yield line
            else:
                raise ValueError(f"Erroneous element for `dub` at index {i}: expected str or Utterance, but was\n{line}")


    def dub(self, lines: Union[str, Utterance, Iterable[Union[str,Utterance]]], voice: str) -> Audio:
        fnames = []
        texts = []
        path = Loc.temp_folder / 'dubbing_service'
        os.makedirs(path, exist_ok=True)
        for line in self._iterate_mixed_arguments(lines):
            if isinstance(line, Utterance):
                audio = self.dub_utterance(line, voice)
            else:
                audio = self.dub_string(line, voice)
            fname = path/(str(uuid4())+'.wav')
            with open(fname, 'wb') as stream:
                stream.write(audio.data)
            fnames.append(fname)
            texts.append(audio.text)
        output_file = path/(str(uuid4())+'.wav')
        FFmpegTools.concat_audio_with_ffmpeg(fnames, output_file)
        with open(output_file,'rb') as stream:
            buffer = stream.read()
        for fname in fnames:
            os.unlink(fname)
        os.unlink(output_file)
        return Audio(buffer, ' '.join(texts))


    def preview(self, lines: Union[str, Utterance, Iterable[Union[str,Utterance]]], voice: str) -> None:
        pass


@dataclasses.dataclass
class DubbingServiceCacheElement:
    pack: BrainBoxTaskPack
    timestamp: datetime.datetime


class BrainBoxDubbingService(IDubbingService):
    def __init__(self,
                 task_generator: Callable[[str, str], BrainBoxTaskPack],
                 brain_box_api: BrainBoxWebApi,
                 cache_ttl_in_seconds: float = 10*60
                 ):
        self.task_generator = task_generator
        self.brain_box_api = brain_box_api
        self.cache: Dict[Tuple[str, str], DubbingServiceCacheElement] = {}
        self.cache_ttl_in_minutes = cache_ttl_in_seconds


    def _try_from_cache(self, s: str, voice: str):
        for key in list(self.cache):
            if (datetime.datetime.now() - self.cache[key].timestamp).total_seconds() > self.cache_ttl_in_minutes:
                del self.cache[key]
        key = (s, voice)
        if key not in self.cache:
            return None
        try:
            result = self.brain_box_api.join(self.cache[key].pack)
            return result
        except:
            del self.cache[key]
        return None


    def dub_string(self, s: str, voice: str) -> Audio:
        cache_result = self._try_from_cache(s, voice)
        if cache_result is not None:
            return Audio(cache_result, text=s)
        task = self.task_generator(s,  voice)
        self.cache[(s, voice)] = DubbingServiceCacheElement(task, datetime.datetime.now())
        result = self.brain_box_api.execute(task)
        return Audio(result, text=s)



    def preview(self, lines: Union[str, Utterance, Iterable[Union[str,Utterance]]], voice:str) -> None:
        tasks = []
        for line in self._iterate_mixed_arguments(lines):
            if isinstance(line, Utterance):
                s = line.to_str()
            else:
                s = line
            task = self.task_generator(s, voice)
            self.cache[(s, voice)] = DubbingServiceCacheElement(task, datetime.datetime.now())
            tasks.append(task)
        for pack in tasks:
            self.brain_box_api.add(pack)


def open_tts_task_generator(text, voice):
    return BrainBoxTaskPack(
        BrainBoxTask(
            id=BrainBoxTask.safe_id(),
            decider='OpenTTS',
            arguments=dict(voice='coqui-tts:en_vctk', lang='en', speakerId=voice, text=text)
        ),
        (),
        DownloadingPostprocessor(take_element_before_downloading=0, opener=FileIO.read_bytes)
    )