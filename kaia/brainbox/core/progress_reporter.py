from ...infra.comm import IMessenger
from abc import ABC, abstractmethod
import sys
from tqdm import tqdm, tqdm_notebook
from tqdm import tqdm
from tqdm.notebook import tqdm as tqdm_notebook

class IProgressReporter(ABC):
    @abstractmethod
    def report_progress(self, progress: float):
        pass

    @abstractmethod
    def log(self, s):
        pass

    def finish(self):
        pass

    def process_externals(self):
        pass


class AbortedException(Exception):
    def __init__(self):
        super(AbortedException, self).__init__('Task was aborted')



class ConsoleProgressReporter(IProgressReporter):
    def report_progress(self, progress: float):
        print(progress)

    def log(self, s):
        print(s)


def _isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False

class EmptyProgressReporter(IProgressReporter):
    def report_progress(self, progress: float):
        pass

    def finish(self):
        pass

    def log(self, s):
        pass

    def process_externals(self):
        pass


class TqdmProgressReporter(IProgressReporter):
    def __init__(self):
        if not _isnotebook():
            ctor = tqdm
        else:
            ctor = tqdm_notebook
        self.progress_bar = ctor(
            total=100,
            unit=" %",
        )
        self.value = 0

    def report_progress(self, progress: float):
        progress=int(progress*100)
        delta = progress-self.value
        self.value=progress
        self.progress_bar.update(delta)

    def finish(self):
        self.progress_bar.close()

    def log(self, s):
        pass


class MessengerProgressReporter(IProgressReporter):
    def __init__(self, id: str, messenger: IMessenger):
        self.id = id
        self.messenger = messenger

    def process_externals(self):
        self.messenger.read_all_and_close('is_alive')
        terminate = self.messenger.read_all_and_close('terminate')
        if len(terminate) > 0:
            sys.exit()
        if self.id is not None:
            if IMessenger.Query(tags=['aborted', self.id]).query_count(self.messenger) > 0:
                raise AbortedException()

    def report_progress(self, progress: float):
        self.process_externals()
        self.messenger.add(progress, 'progress', self.id)

    def log(self, s):
        self.process_externals()
        self.messenger.add(s, 'log', self.id)
