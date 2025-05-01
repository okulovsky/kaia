from yo_fluq import FileIO
from ...upsampling import UpsamplingItem, StringDistance
from .exporter import ExportItem
from dataclasses import dataclass
from brainbox import BrainBox
from chara.tools.wav_processor import WavProcessor
from .exporter import IExporter
import numpy as np

@dataclass
class TrimExporter(IExporter):
    api: BrainBox.Api
    distance: StringDistance
    trim_text_start: str
    trim_text_end: str
    max_vosk_trim: int
    time_margin_in_seconds: float|None = None
    max_interword_margin: float|None = None
    character: str | None = None


    def fix_text(self, file: UpsamplingItem):
        if not file.voiceover_tags['text'].startswith(self.trim_text_start) or not file.voiceover_tags['text'].endswith(self.trim_text_end):
            return None
        text: str = file.voiceover_tags['text']
        text = text[len(self.trim_text_start):-len(self.trim_text_end)]
        return text

    def find_vosk_trim(self, fixed_text: str, vosk:list[dict]) -> tuple[int,int]:
        best_candidate = None
        best_distance = None
        for start_trim in range(0, self.max_vosk_trim + 1):
            for end_trim in range(0, self.max_vosk_trim + 1):
                vosk_text = ' '.join(w['word'] for w in vosk[start_trim:-end_trim])
                d = self.distance.distance(fixed_text, vosk_text)
                if best_distance is None or d < best_distance:
                    best_candidate = (start_trim, end_trim)
                    best_distance = d

        start_index, end_index = best_candidate
        end_index = len(vosk) - end_index
        return start_index, end_index




    def _remove_interword_silence(
            self,
            wav_processor: WavProcessor,
            vosk: list[dict]
    ):
        cut_margin = self.max_interword_margin/4
        fade_margin = self.max_interword_margin/4
        proc = wav_processor

        current = vosk[0]['start']
        buffer = [[]]
        for v in vosk:
            if (v['start'] - current) > self.max_interword_margin:
                buffer.append([])
            buffer[-1].append(v)
            current = v['end']

        frames = []
        for i, seq in enumerate(buffer):
            start = seq[0]['start']
            end = seq[-1]['end']

            if i != 0:
                frames.append(proc.fade(proc.cut(start - cut_margin - fade_margin, start - cut_margin), 0, 1))
            frames.append(proc.cut(start - cut_margin, end + cut_margin))
            if i != len(buffer) - 1:
                frames.append(proc.fade(proc.cut(end + cut_margin, end + cut_margin + fade_margin), 1, 0))

        wav = proc.frames_to_wav_bytes(np.vstack(frames))
        return wav

    def _simple_cut(self, wav_processor: WavProcessor, vosk, start_index, end_index):
        pre_start = vosk[start_index - 1]
        start = vosk[start_index]
        end = vosk[end_index-1]
        post_end = vosk[end_index]

        start_timestamp = (start['start'] + pre_start['end']) / 2
        if self.time_margin_in_seconds is not None:
            n = start['start'] - self.time_margin_in_seconds
            if n > start_timestamp:
                start_timestamp = n
        end_timestamps = (end['end'] + post_end['start']) / 2
        if self.time_margin_in_seconds is not None:
            n = end['end'] + self.time_margin_in_seconds
            if n < end_timestamps:
                end_timestamps = n

        cropped = wav_processor.cut(start_timestamp, end_timestamps)
        return wav_processor.frames_to_wav_bytes(cropped)

    def export(self, file: UpsamplingItem) -> ExportItem:
        text = self.fix_text(file)
        start_index, end_index = self.find_vosk_trim(text, file.vosk)

        duration = file.vosk[end_index]['end'] - file.vosk[start_index]['start']
        item = ExportItem(
            file.voiceover_file,
            file.voiceover_tags['character'],
            text,
            duration,
            (file.vosk, start_index, end_index)
        )
        return item

    def get_content(self, item: ExportItem) -> bytes:
        vosk, start_index, end_index = item.content_description

        wav = self.api.download(item.filename)
        proc = WavProcessor(wav)

        if self.max_interword_margin is None:
            return self._simple_cut(proc, vosk, start_index, end_index)
        else:
            return self._remove_interword_silence(proc, vosk[start_index:end_index])



