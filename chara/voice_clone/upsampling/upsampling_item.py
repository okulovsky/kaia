from dataclasses import dataclass
import pandas as pd
from ..voice_cloner import VoiceCloner


@dataclass
class Statistics:
    distance: int


@dataclass
class UpsamplingItem:
    text: str
    voice_cloner: VoiceCloner|None = None
    voiceover_file: str|None = None
    voiceover_tags: dict|None = None
    vosk: list[dict]|None = None
    resemblyzer: dict | None = None
    statistics: Statistics|None = None
    selected: bool | None = None

    @staticmethod
    def to_df(records: list['UpsamplingItem']) -> pd.DataFrame:
        rows = []
        for record in records:
            row=dict(file=record.voiceover_file)
            for d in [record.statistics.__dict__, record.voiceover_tags]:
                for key, value in d.items():
                    row[key]=value
            row['selected'] = record.selected
            row['duration'] = record.vosk[-1]['end'] - record.vosk[0]['start']
            rows.append(row)
        return pd.DataFrame(rows)



