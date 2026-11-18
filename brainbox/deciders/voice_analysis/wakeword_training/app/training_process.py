"""Stream server stage changes without blocking progress for the whole run."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError

from foundation_kaia.brainbox_utils import BrainboxReportItem


class TrainingProcess:
    def __init__(self, runtime):
        self.runtime = runtime

    def run(self, training_id, parameters, expected, dataset):
        stages = [
            "receiving",
            "preflight",
            "training",
            "selecting",
            "exporting",
            "evaluating",
            "reporting",
            "complete",
        ]
        previous = None
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                self.runtime.train, training_id, parameters, expected, dataset
            )
            while True:
                try:
                    result = future.result(timeout=1)
                    yield BrainboxReportItem(progress=1.0, result=result)
                    return
                except TimeoutError:
                    if future.done():
                        raise
                    state = self.runtime.describe(training_id)
                    stage = state.get("status", "receiving")
                    if stage != previous:
                        previous = stage
                        progress = (
                            stages.index(stage) / len(stages)
                            if stage in stages
                            else 0.0
                        )
                        yield BrainboxReportItem(
                            log="Wakeword stage: " + stage, progress=progress
                        )
