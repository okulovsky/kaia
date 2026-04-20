from typing import TypeVar, Generic, Any
from brainbox import BrainBox
from dataclasses import dataclass

TCase = TypeVar("TCase")
TOption = TypeVar("TOption")

@dataclass
class BrainBoxPipelineResultOption(Generic[TOption]):
    brainbox_option: Any
    option: TOption|None = None
    merge_error: Exception|None = None



@dataclass
class BrainBoxPipelineResultItem(Generic[TCase, TOption]):
    case: TCase
    task: BrainBox.Task|None = None
    brainbox_answer_is_missing: bool = False
    brainbox_error: str|None = None
    brainbox_result: Any = None
    divider_error: Exception|None = None
    options: list[BrainBoxPipelineResultOption[TOption]]|None = None
