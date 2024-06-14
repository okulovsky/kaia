from abc import ABC, abstractmethod
import threading
import subprocess

class IProcessController(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def terminate(self, thread: threading.Thread):
        pass

    @abstractmethod
    def get_output(self):
        pass

    @abstractmethod
    def has_exited(self):
        pass



class SubprocessController(IProcessController):
    def __init__(self, arguments):
        self.arguments = arguments
        self.process: subprocess.Popen | None = None
        self.exited = False

    def start(self):
        self.process = subprocess.Popen(
            self.arguments,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        self.process.wait()
        self.exited = True

    def terminate(self, thread):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        if thread is not None:
            thread.join()

    def has_exited(self):
        if self.process is None:
            return True
        return self.exited

    def get_output(self):
        return ''