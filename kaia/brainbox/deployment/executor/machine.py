from dataclasses import dataclass
from pathlib import Path

@dataclass
class Machine:
    is_windows: int
    user_id: int
    group_id: int
    vram_in_gb: None|int
    data_folder: Path
    ip_address: str
    username: str
