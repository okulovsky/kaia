import sys
from pathlib import Path
import threading
import os
import json
from datetime import datetime

lock = threading.Lock()


class KaiaLog:
    _log_file: Path | None = None

    @staticmethod
    def setup(log_file: Path):
        KaiaLog._log_file = log_file

    @staticmethod
    def write(type: str, content = None):
        dt = datetime.now()
        print(f'{dt} [{type}] {content}')
        sys.stdout.flush()
        with lock:
            if KaiaLog._log_file is not None:
                os.makedirs(KaiaLog._log_file.parent, exist_ok=True)
                with open(KaiaLog._log_file, 'a') as file:
                    file.write(json.dumps(dict(type=str(type), timestamp=str(dt), content=str(content))))
                    file.write('\n')





