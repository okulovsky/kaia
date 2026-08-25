from dataclasses import dataclass

@dataclass
class TreeStatus:
    is_selected: bool = False
    is_root: bool = False