from abc import ABC, abstractmethod

class INotebookableController(ABC):
    @abstractmethod
    def run_notebook(self):
        pass

