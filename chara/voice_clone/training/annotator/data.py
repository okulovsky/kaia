from yo_fluq import *
from ..exporters import ExportItem


class Data:
    def __init__(self,
                 data: list[ExportItem],
                 allowed_text_indices: Iterable[int] | None = None
                 ):
        self.data = data

        texts = set([item.text for item in data])
        self.text_to_index = {text: index for index, text in enumerate(texts)}
        self.voices = list(set(item.character for item in data))
        self.file_to_data = {item.filename: item for item in data}

        self.solved_files = set()
        self.solved_texts = set()
        self.bad_sentences = set()
        self.voice_to_duration = {voice:0 for voice in self.voices}

        self.allowed_text_indices = allowed_text_indices
        if self.allowed_text_indices is None:
            self.allowed_text_indices = set(self.text_to_index.values())


    def get_available(self, current_voice):
        allowed = []
        total = 0
        for item in self.data:
            text = item.text
            idx = self.text_to_index[text]
            if idx not in self.allowed_text_indices:
                continue
            character = item.character
            if character != current_voice:
                continue
            total += 1

            if item.filename in self.solved_files:
                continue
            if text in self.bad_sentences:
                continue
            if (character, text) in self.solved_texts:
                continue

            allowed.append(item)
        return allowed, total