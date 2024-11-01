from typing import *
from ..installer import IInstaller
from dataclasses import dataclass

class OneOrNoneModelWarmuper:
    @dataclass
    class Status:
        is_running: bool
        current_model: str|None


    def __init__(self,
                 installer_get_status: Optional[Callable[[IInstaller], 'OneOrNoneModelWarmuper.Status']] = None,
                 installer_run_with_model: Optional[Callable[[IInstaller, Union[str]], None]] = None,
                 ):
        self.installer_get_status = installer_get_status
        self.installer_run_with_model = installer_run_with_model

    def _post_load_check(self, installer: IInstaller, due_name: str|None):
        after_load_status = self.installer_get_status(installer)
        if not after_load_status.is_running:
            raise ValueError("Installer didn't run")
        if due_name is not None:
            if after_load_status.current_model != due_name:
                raise ValueError(f"Failed warmup: ordered to load {due_name}, but actually {after_load_status.current_model} was loaded")
        return after_load_status.current_model


    def load_model(self, installer: IInstaller, due_name: str|None):
        status = self.installer_get_status(installer)
        if not status.is_running:
            self.installer_run_with_model(installer, due_name)
            self._post_load_check(installer,due_name)
            return
        if due_name is None:
            return
        if status.current_model == due_name:
            return
        self.installer_run_with_model(installer, due_name)
        self._post_load_check(installer,due_name)


    def check_and_return_running_model(self, installer: IInstaller, due_name: str|None) -> Any:
        return self._post_load_check(installer, due_name)



