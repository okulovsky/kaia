"""Normalize legacy checkpoint tokenizer module names without changing weights."""

import pickle
import types
from pathlib import Path


class TokenizerUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "deep_phonemizer.preprocessing.text" and name in (
            "LanguageTokenizer",
            "SequenceTokenizer",
            "Preprocessor",
        ):
            module = "dp.preprocessing.text"
        return super().find_class(module, name)


def prepare_checkpoint(source, destination):
    import torch
    from dp.phonemizer import Phonemizer

    serializer = types.ModuleType("wakeword_legacy_checkpoint")
    serializer.Unpickler = TokenizerUnpickler
    serializer.load = pickle.load
    serializer.loads = pickle.loads
    serializer.dump = pickle.dump
    serializer.dumps = pickle.dumps
    checkpoint = torch.load(str(source), map_location="cpu", pickle_module=serializer)
    target = Path(destination)
    temporary = target.with_suffix(".partial.pt")
    torch.save(checkpoint, temporary)
    model = Phonemizer.from_checkpoint(str(temporary))
    del model, checkpoint
    temporary.replace(target)
    return target
