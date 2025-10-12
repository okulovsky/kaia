from dataclasses import dataclass, field
from pathlib import Path
from brainbox.framework.deployment.executor import IExecutor, LocalExecutor

@dataclass
class BuildContext:
    root_path: Path
    executor: IExecutor|None = None

    @property
    def requirements_original(self):
        return self.root_path/'requirements.txt'


    @property
    def requirements_lock(self):
        return self.root_path/'requirements.lock.txt'

    @property
    def requirements_preinstall(self):
        return self.root_path/'requirements.build.txt'

    @property
    def repo_fix_folder(self):
        return self.root_path/'repo_fix'

    @property
    def app_folder(self):
        return self.root_path/'app'