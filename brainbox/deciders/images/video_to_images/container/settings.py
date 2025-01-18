from dataclasses import dataclass

@dataclass
class AnalysisSettings:
    source_file_name: str
    max_produced_frames: int|None = None
    buffer_by_laplacian_in_ms: int|None = None
    add_comparator: bool = False