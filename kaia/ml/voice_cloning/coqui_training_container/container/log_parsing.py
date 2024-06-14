from typing import *
import re
from dataclasses import dataclass, field


epoch_re = re.compile('EPOCH: (\d+)/(\d+)')

class partition_by_header:
    def __init__(self, condition):
        self.condition = condition

    def __call__(self, en):
        buffer = None
        for i in en:
            if self.condition(i):
                if buffer is not None:
                    yield buffer
                buffer = [i]
            else:
                if buffer is not None:
                    buffer.append(i)
        yield buffer

glob_step_re = re.compile('STEP: \d+/\d+ -- GLOBAL_STEP: (\d+)')
metric_re = re.compile('\| > ([a-z0-9_]+):[^ ]* ([\d\.]+)')

@dataclass
class EpochLog:
    iteration: int = -1
    epoch: int = -1
    step: int = -1
    train_metrics: Dict[str, float] = field(default_factory=dict)
    eval_metrics: Dict[str, float] = field(default_factory=dict)
    exception: List[str] = field(default_factory=list)


class Parser:
    def __init__(self):
        self.iteration = 0

    def parse_epoch(self, lines):
        if lines is None:
            return None
        ep = EpochLog()
        in_eval = False
        in_exception = False
        for line in lines:
            s = epoch_re.search(line)
            if s is not None:
                ep.epoch = int(s.group(1))
                continue
            s = glob_step_re.search(line)
            if s is not None:
                ep.step = int(s.group(1))
                continue
            if 'exception' in line.lower():
                in_exception = True
            if in_exception:
                ep.exception.append(line)
                continue
            if 'EVALUATION' in line:
                in_eval = True
            s = metric_re.search(line)
            if s is not None:
                d = ep.eval_metrics if in_eval else ep.train_metrics
                d[s.group(1)] = float(s.group(2))
        if ep.epoch == 0:
            self.iteration += 1
        ep.iteration = self.iteration
        return ep


def parse(file):
    with open(file,'r') as stream:
        lines = stream.readlines()
    parser = Parser()

    parsed = []
    buffer = []
    for line in lines:
        if epoch_re.search(line) is not None:
            if len(buffer) > 0:
                parsed.append(parser.parse_epoch(buffer))
                buffer = []
        buffer.append(line)

    if len(buffer) > 0:
        parsed.append(parser.parse_epoch(buffer))

    return parsed