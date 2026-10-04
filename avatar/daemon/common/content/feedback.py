import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping
from yo_fluq import FileIO
from foundation_kaia.marshalling import IStorage

_EMPTY: Mapping[str, Any] = MappingProxyType({})


class Feedback:
    def __init__(self, data: dict[str, dict[str, Any]]|None = None):
        self._data = {
            file_id: MappingProxyType(dict(values))
            for file_id, values in (data or {}).items()
        }

    def __getitem__(self, file_id: str) -> Mapping[str, Any]:
        return self._data.get(file_id, _EMPTY)

    def __contains__(self, file_id: str) -> bool:
        return file_id in self._data

    def __len__(self) -> int:
        return len(self._data)

    def get(self, file_id: str, key: str, default: Any = 0) -> Any:
        return self._data.get(file_id, _EMPTY).get(key, default)

    def ids(self) -> Iterable[str]:
        return self._data.keys()

    def items(self) -> Iterable[tuple[str, Mapping[str, Any]]]:
        return self._data.items()

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {file_id: dict(values) for file_id, values in self._data.items()}

    def __repr__(self):
        return f'Feedback({self.to_dict()})'


class IFeedbackStorage(ABC):
    @abstractmethod
    def load(self) -> Feedback:
        pass

    @abstractmethod
    def save(self, feedback: Feedback) -> None:
        pass

    def append(self, file_id: str, values: dict[str, Any]) -> Feedback:
        data = self.load().to_dict()
        entry = data.setdefault(file_id, {})
        for key, value in values.items():
            entry[key] = entry.get(key, 0) + value
        feedback = Feedback(data)
        self.save(feedback)
        return feedback


class InMemoryFeedbackStorage(IFeedbackStorage):
    def __init__(self, feedback: Feedback|None = None):
        self.feedback = feedback if feedback is not None else Feedback()

    def load(self) -> Feedback:
        return self.feedback

    def save(self, feedback: Feedback) -> None:
        self.feedback = feedback


class FileFeedbackStorage(IFeedbackStorage):
    def __init__(self, path: Path|str):
        self.path = Path(path)

    def load(self) -> Feedback:
        if not self.path.is_file():
            return Feedback()
        return Feedback(FileIO.read_json(self.path))

    def save(self, feedback: Feedback) -> None:
        os.makedirs(self.path.parent, exist_ok=True)
        FileIO.write_json(feedback.to_dict(), self.path)


class StorageFeedbackStorage(IFeedbackStorage):
    def __init__(self, storage: IStorage, filename: str):
        self.storage = storage
        self.filename = filename

    def load(self) -> Feedback:
        if not self.storage.is_file(self.filename):
            return Feedback()
        return Feedback(json.loads(self.storage.read(self.filename)))

    def save(self, feedback: Feedback) -> None:
        self.storage.upload(self.filename, json.dumps(feedback.to_dict()).encode('utf-8'))
