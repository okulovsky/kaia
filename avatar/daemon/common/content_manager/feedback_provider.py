import os
from pathlib import Path
from yo_fluq import FileIO
from abc import ABC, abstractmethod

class IFeedbackProvider(ABC):
    @abstractmethod
    def load_feedback(self) -> dict:
        pass

    @abstractmethod
    def save_feedback(self, feedback: dict):
        pass

    def append_feedback(self, file_id: str, values: dict[str, int]):
        feedback = self.load_feedback()
        if file_id not in feedback:
            feedback[file_id] = values
        else:
            for key, value in values.items():
                feedback[file_id][key] = feedback[file_id].get(key,0) + value
        self.save_feedback(feedback)

class InMemoryFeedbackProvider(IFeedbackProvider):
    def __init__(self):
        self.feedback = {}

    def load_feedback(self) -> dict:
        return self.feedback

    def save_feedback(self, feedback: dict):
        self.feedback = feedback


class FileFeedbackProvider(IFeedbackProvider):
    def __init__(self, path):
        self.path = Path(path)

    def load_feedback(self):
        if not self.path.is_file():
            return {}
        return FileIO.read_json(self.path)

    def save_feedback(self, feedback):
        os.makedirs(self.path.parent, exist_ok=True)
        FileIO.write_json(feedback, self.path)










