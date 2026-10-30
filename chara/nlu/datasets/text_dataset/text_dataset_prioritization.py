from collections import Counter
from pathlib import Path
from chara.common import Chara, CasePrioritization
from .text_dataset_pipeline import TextDatasetCase, TextDatasetFingerprint


class TextDatasetPrioritization(CasePrioritization[TextDatasetCase, TextDatasetFingerprint]):
    """`existing` is the number of paraphrased templates with this fingerprint in the finished runs of `positives_folder`"""

    def __init__(self,
                 positives_folder: Path,
                 strategy: CasePrioritization.Strategy,
                 budget: int,
                 max_cases_per_fingerprint: int|None = None,
                 ):
        super().__init__(strategy, budget, max_cases_per_fingerprint)
        self.positives_folder = positives_folder

    def collect_statistics(self, fingerprints):
        counts = Counter()
        if self.positives_folder.is_dir():
            for run in self.positives_folder.iterdir():
                if not run.is_dir():
                    continue
                run_folder = Chara.from_folder(run)
                if run_folder.has_result:
                    counts.update(case.to_fingerprint() for case in run_folder.result)
        for fingerprint, item in fingerprints.items():
            item.existing = counts[fingerprint]
