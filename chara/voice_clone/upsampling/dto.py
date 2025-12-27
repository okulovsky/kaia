from pathlib import Path
from dataclasses import dataclass


@dataclass
class VerifierResult:
    distance: int
    slice: list[dict]
    duration: float
    allowed: bool
    start_index: int
    end_index: int
    recognition: list[dict]

    @property
    def recognition_as_str(self):
        return ' '.join(r['word'] for r in self.recognition)

    def get_audio_cut(self) -> tuple[float|None, float|None]:
        if self.start_index == 0:
            trim_start = None
        else:
            trim_start = (
                self.recognition[self.start_index]['start'] +
                self.recognition[self.start_index-1]['end']
            )/2

        if self.end_index == len(self.recognition):
            trim_end = None
        else:
            trim_end = (
                self.recognition[self.end_index]['start'] +
                self.recognition[self.end_index-1]['end']
            )/2

        return trim_start, trim_end




@dataclass
class UpsamplingResult:
    verification: VerifierResult
    text: str
    path_to_file: Path
