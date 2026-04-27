import ctypes
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid

class ISideProcess(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def get_html_report(self):
        pass

@dataclass
class SideProcessInstance:
    process: ISideProcess
    thread: threading.Thread
    exception: Exception | None = None


class SideProcessPool:
    def __init__(self):
        self.id_to_instance: dict[str, SideProcessInstance] = {}
        self.id_to_report: dict[str, str] = {}

    def start(self, process: ISideProcess) -> str:
        key = str(uuid.uuid4())
        instance = SideProcessInstance(process, None)

        def _target():
            try:
                process.run()
            except Exception as e:
                instance.exception = e

        thread = threading.Thread(target=_target, daemon=True)
        instance.thread = thread
        self.id_to_instance[key] = instance
        self.id_to_report[key] = ''
        thread.start()
        return key

    def update(self):
        for key in list(self.id_to_instance.keys()):
            instance = self.id_to_instance[key]
            if not instance.thread.is_alive():
                self.id_to_report[key] = instance.process.get_html_report()
                del self.id_to_instance[key]


    def is_running(self, key: str) -> bool:
        self.update()
        return key in self.id_to_instance

    def active_processes(self) -> int:
        self.update()
        return len(self.id_to_instance)

    def get_report(self, key: str):
        self.update()
        if key in self.id_to_instance:
            self.id_to_report[key] = self.id_to_instance[key].process.get_html_report()
        return self.id_to_report[key]

    def join(self, key: str):
        self.update()
        if key not in self.id_to_instance:
            return
        instance = self.id_to_instance[key]
        instance.thread.join()
        self.update()
        if instance.exception is not None:
            raise instance.exception

    def terminate(self, key: str):
        self.update()
        if key not in self.id_to_instance:
            return
        instance = self.id_to_instance[key]
        while instance.thread.is_alive():
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(instance.thread.ident),
                ctypes.py_object(KeyboardInterrupt),
            )
            instance.thread.join(timeout=0.1)
        self.update()





