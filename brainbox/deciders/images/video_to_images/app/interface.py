from foundation_kaia.marshalling import service, FileLike
from foundation_kaia.brainbox_utils import BrainboxReportItem, brainbox_websocket, brainbox_endpoint
from typing import Iterable
from dataclasses import dataclass

@dataclass
class AnalysisSettings:
    source_file_name: str = ''
    max_produced_frames: int|None = None
    buffer_by_laplacian_in_ms: int|None = None
    add_simple_comparator: bool = False
    add_semantic_comparator: bool = False


@service
class VideoToImagesInterface:
    @brainbox_websocket
    def process(self, video: FileLike, settings: AnalysisSettings) -> Iterable[BrainboxReportItem[list[dict]]]:
        """Extracts frames from a video according to the analysis settings, streaming progress."""
        ...

    @brainbox_endpoint
    def get_tar(self) -> FileLike:
        """Returns the last processed frame set as a tar archive."""
        ...
