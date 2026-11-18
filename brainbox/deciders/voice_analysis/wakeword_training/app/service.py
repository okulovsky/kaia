"""Thin service boundary around independent server stages."""

from uuid import uuid4

from foundation_kaia.brainbox_utils import BrainboxReportItem
from foundation_kaia.marshalling import FileLikeHandler

try:
    from . import interface as contract
except ImportError:
    import interface as standalone_contract

    contract = standalone_contract


class WakewordTrainingService(contract.IWakewordTraining):
    def __init__(self, installer):
        self.installer = installer
        try:
            from wakeword_core.server import ServerTraining
        except ImportError:
            from brainbox.deciders.voice_analysis.wakeword_training.runtime.server import (
                ServerTraining,
            )
        self.runtime = ServerTraining(installer.resources_folder)

    def readiness(self):
        return self.installer.readiness()

    def describe(self, training_id):
        return self.runtime.describe(training_id)

    def train(self, training_id, parameters, expected_dataset, dataset):
        if not self.readiness()["ready"]:
            raise RuntimeError("resource_not_ready: run prepare")
        folder = self._receive_dataset(training_id, dataset)
        yield BrainboxReportItem(progress=0.0)
        if __package__:
            from .training_process import TrainingProcess
        else:
            from training_process import TrainingProcess
        yield from TrainingProcess(self.runtime).run(
            training_id, parameters, expected_dataset, folder
        )

    def _receive_dataset(self, training_id, dataset):
        try:
            from wakeword_core.archives import BUDGET, extract_archive
            from wakeword_core.manifests import FILES
        except ImportError:
            from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
                BUDGET,
                extract_archive,
            )
            from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
                FILES,
            )
        root = self.runtime.folder(training_id)
        incoming = root / "incoming" / uuid4().hex
        incoming.mkdir(parents=True)
        path = incoming / "dataset.zip"
        size = 0
        with path.open("xb") as output:
            for chunk in FileLikeHandler.to_bytes_iterable(dataset):
                size += len(chunk)
                if size > BUDGET:
                    raise ValueError("dataset exceeds upload budget")
                output.write(chunk)
        return extract_archive(path, incoming / "dataset", FILES)

    def export(self, result):
        from json import loads

        root = self.runtime.folder(result["training_id"])
        reference = root / "reference.json"
        if not reference.exists() or loads(reference.read_text()) != result:
            raise ValueError("result reference mismatch")
        path = root / "artifacts/result.zip"
        if not path.exists():
            raise ValueError("result_missing")
        return path
