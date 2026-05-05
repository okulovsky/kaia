from ..core import IAnnotationCache, AnnotationStatus
from pathlib import Path
from ....architecture.result_handling import write_result, find_result
from ....architecture import Chara


class LabelAnnotationCache(IAnnotationCache):
    def __init__(self, folder: Path):
        self.folder = folder


    @property
    def ready(self) -> bool:
        return find_result(self.folder) is not None or  (self.folder/'.finished').is_file()

    @property
    def temp_file(self) -> Path:
        return self.folder/'annotation.txt'

    def _update(self, s: str):
        with open(self.temp_file, 'a') as file:
            file.write(s+"\n")


    def add(self, id: str, label: str):
        if self.ready:
            raise ValueError("Cannot update the finalized annotation")
        self._update(f'#{id}: {label}')

    def skip(self, id: str):
        if self.ready:
            raise ValueError("Cannot update the finalized annotation")
        self._update(f'!SKIP {id}')

    def undo(self):
        if self.ready:
            raise ValueError("Cannot update the finalized annotation")

        with open(self.temp_file, 'r') as stream:
            lines = stream.readlines()

        if len(lines) == 0:
            return

        with open(self.temp_file, 'w') as stream:
            stream.writelines(lines[:-1])

    def finish_annotation(self):
        (self.folder/'.finished').write_text('')

    def get_annotation_status(self) -> dict[str, AnnotationStatus]:
        file = find_result(self.folder)
        if file is None:
            file = self.temp_file

        if not file.exists():
            return {}

        statuses = {}

        def _get(id: str) -> AnnotationStatus:
            if id not in statuses:
                statuses[id] = AnnotationStatus()
            return statuses[id]

        with open(file, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if line.startswith('#'):
                    key, value = line[1:].split(':')
                    _get(key).value = value.strip()
                elif line.startswith('!SKIP'):
                    id = line[len('!SKIP'):].strip()
                    _get(id).skipped_times += 1

        return statuses

    def get_summary(self) -> str:
        result = {}
        status = self.get_annotation_status()
        for id, annotation in status.items():
            if annotation.value is not None:
                if annotation.value not in result:
                    result[annotation.value] = 0
                result[annotation.value] += 1
        return ' '.join(f'{k}:{v}' for k, v in result.items())

    def get_result(self) -> dict[str, str]:
        return {key:annotation.value for key, annotation in self.get_annotation_status().items() if annotation.value is not None}