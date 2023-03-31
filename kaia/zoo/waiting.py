from ..infra.tasks import ITask, ProgressReporter
import time

class Waiting(ITask):
    def __init__(self, time_delta: float):
        self.time_delta = time_delta
        self.warmed_up = False

    def warm_up(self):
        self.warmed_up = True

    def run(self, reporter: ProgressReporter, ticks: int):
        ticks = int(ticks)
        reporter.log(f'Warmed up {self.warmed_up}')
        for tick in range(ticks):
            reporter.report_progress(tick/ticks)
            reporter.log(f'Tick {tick}/{ticks}')
            time.sleep(self.time_delta)
        return ticks+1
