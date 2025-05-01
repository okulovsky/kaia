import copy

from brainbox.flow import IStep
from .string_distance import StringDistance
from .upsampling_item import UpsamplingItem
from dataclasses import dataclass
import traceback

@dataclass
class VoskStatistics:
    file: str|None = None
    true_text: str|None = None
    recognized_text: str | None = None
    distances: str | None = None
    selected: str | None = None
    error: str|None = None


class VoskStatisticsStep(IStep):
    def __init__(self,
                 distance: StringDistance,
                 max_allowed_distance: int|None = None
                 ):
        self.distance = distance
        self.max_allowed_distance = max_allowed_distance

    def _create_statistics(self, item: UpsamplingItem):
        row = VoskStatistics()
        try:
            row.file = item.voiceover_file
            row.true_text = item.voiceover_tags['text']
            row.recognized_text = ' '.join(v['word'] for v in item.vosk)
            row.distance = self.distance.distance(row.true_text, row.recognized_text)
            selected = True
            if self.max_allowed_distance is not None and row.distance > self.max_allowed_distance:
                selected = False
            row.selected = selected
            row.error = None
        except:
            row.selected = False
            row.error = traceback.format_exc()
        return row

    def process(self, history, current: list[UpsamplingItem]):
        result = []
        for item in current:
            item = copy.copy(item)
            item.statistics = self._create_statistics(item)
            item.selected = item.statistics.selected
            result.append(item)
        return result

    def summarize(self, data) -> str|None:
        total = len(data)
        good = sum(1 for item in data if item.selected)
        return f'selected {good}/{total}, {int(100*good/total)}% success rate'


