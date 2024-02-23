from abc import ABC, abstractmethod
import subprocess
import threading
import signal

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




class WslProcessController(IProcessController):
    def __init__(self,
                 command: str,
                 distributive: str = 'Ubuntu',
                 shutdown_wsl: bool = False
                 ):
        self.command = command
        self.distributive = distributive
        self.shutdown_wsl = shutdown_wsl
        self.output = ''
        self.error = ''


    def start(self):
        self.process = subprocess.Popen(
            ['wsl','-d',self.distributive],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        self.output, self.error = self.process.communicate(self.command.encode('ascii'), timeout=None)


    def terminate(self, thread: threading.Thread):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        if thread is not None:
            thread.join()
        if self.shutdown_wsl:
            subprocess.call(['wsl', '--shutdown'])


    def get_output(self):
        output = self.output
        if output is None:
            output = ''
        elif not isinstance(output, str):
            output = output.decode('utf-8')
        error = self.error
        if error is None:
            error = ''
        elif not isinstance(error, str):
            error = error.decode('utf-8')
        return output+'\n\n'+error


