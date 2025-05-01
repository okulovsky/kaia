from typing import *
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from yo_fluq import *
import os

class BaseAnnotator(ABC):
    @dataclass
    class Sample:
        id: str|None
        controls: Any

    def __init__(self, path: Path):
        self._current_id: str|None = None
        self._path = Path(path)

    @abstractmethod
    def on_feedback(self, id: str, feedback: str):
        pass

    @abstractmethod
    def get_next(self) -> 'BaseAnnotator.Sample':
        pass



    def cm_feedback(self, feedback: str):
        if self._current_id is None:
            return
        self.on_feedback(self._current_id, feedback)
        os.makedirs(self._path.parent, exist_ok=True)
        with open(self._path, 'a') as stream:
            stream.write(f'{self._current_id}|{feedback}\n')

    def cm_next_sample(self):
        sample = self.get_next()
        self._current_id = sample.id
        return sample.controls


    def cm_load(self):
        if self._path.is_file():
            records = BaseAnnotator.read_annotation_file(self._path)
            for record in records:
                self.on_feedback(record['id'], record['feedback'])

    @staticmethod
    def read_annotation_file(path: Path)->list[dict]:
        return (
            Query.file.text(path)
            .select(str.strip)
            .select(lambda z: z.split('|'))
            .select(lambda z: dict(id=z[0], feedback=z[1]))
            .to_list()
        )




