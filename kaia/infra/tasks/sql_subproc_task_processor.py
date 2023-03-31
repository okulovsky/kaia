import subprocess
from typing import *
from .sql_task_processor import SqlTaskProcessor
import atexit
import os
from ..sql_messenger import SqlMessenger, MessengerQuery
from ..loc import Loc
from uuid import uuid4
import dataclasses
from pathlib import Path
from yo_fluq_ds import FileIO
import time
import sys

@dataclasses.dataclass
class SubprocessConfig:
    task_class_path: str
    task_args: List = dataclasses.field(default_factory=lambda:[])
    task_kwargs: Dict = dataclasses.field(default_factory=lambda:{})
    executable: Path = dataclasses.field(default_factory=lambda: Path(sys.executable))
    sleep: Union[int, float] = 1
    db_path: Optional[Path] = None


class SqlSubprocTaskProcessor(SqlTaskProcessor):
    def __init__(self, config: SubprocessConfig, run_check_attempts = 10):
        if config.db_path is None:
            config.db_path = Loc.temp_folder/f'signalling_db/{uuid4()}'
        os.makedirs(config.db_path.parent, exist_ok=True)
        self.config = config
        messenger = SqlMessenger(config.db_path)
        super(SqlSubprocTaskProcessor, self).__init__(messenger)
        self.process = None
        self.run_check_attempts = run_check_attempts

    def activate(self):
        atexit.register(self.deactivate)
        path = Loc.temp_folder/f'app_configs/{uuid4()}'
        os.makedirs(path.parent, exist_ok=True)
        FileIO.write_jsonpickle(self.config, path)
        id = self.messenger.add(None, 'is_alive')
        self.process = subprocess.Popen([self.config.executable,'-m','kaia.infra.tasks.side_proc_app', path])
        for i in range(10):
            result = MessengerQuery(id=id).query_single(self.messenger)
            if not result.open:
                return
            time.sleep(1)
        raise ValueError('The process did not start successfully')

    def deactivate(self):
        self.process.terminate()
