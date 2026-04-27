from foundation_kaia.brainbox_utils import logger, LongBrainboxProcess
import time

class HelloBrainBoxTrainingProcess(LongBrainboxProcess[str]):
    def __init__(self, raise_exception: bool, pause: float = 0.1, steps: int = 10):
        self.raise_exception = raise_exception
        self.pause = pause
        self.steps = steps

    def execute(self) -> str:
        for i in range(self.steps):
            logger.info(f"Step {i}")
            logger.progress(i/self.steps)
            time.sleep(self.pause)
            if i>=5 and self.raise_exception:
                raise ValueError("Requested exception is raised")
        return 'RESULT'