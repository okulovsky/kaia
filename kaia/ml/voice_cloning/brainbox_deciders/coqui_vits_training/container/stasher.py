import os

from model_file_info import ModelFileInfo
from pathlib import Path
import shutil
from threading import Thread
import time
from service import Service
from utils import get_working_folder

class Stasher(Service):
    def __init__(self,
                 folder: Path,
                 max_allowed_gap_in_steps = 10000,
                 sleep_in_seconds: int = 60
                 ):
        self.max_allowed_gap_in_steps = max_allowed_gap_in_steps
        super().__init__(folder, sleep_in_seconds)


    def _iteration(self):
        models_folder = get_working_folder(self.folder)
        if models_folder is None:
            return

        models = ModelFileInfo.parse_folder(models_folder)
        non_checkpoints = [m.step for m in models if m.type!=ModelFileInfo.Type.Checkpoint]
        checkpoints = [m.step for m in models if m.type == ModelFileInfo.Type.Checkpoint]
        if len(non_checkpoints) == 0 or len(checkpoints) == 0:
            return
        max_stashed = max(non_checkpoints)
        min_checkpoint = min(checkpoints)
        print(f'STASHER FOUND CHECKPOINTS: {checkpoints}')
        if min_checkpoint - max_stashed > self.max_allowed_gap_in_steps:
            try:
                to_move = [m for m in models if m.step == min_checkpoint]
                shutil.move(to_move[0].path, models_folder/f'stash_{min_checkpoint}.pth')
            except:
                pass
