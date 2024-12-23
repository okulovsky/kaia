from ...common import Logger
from ..core import OperatorMessage
from queue import Queue

class DeciderLogger(Logger):
    def __init__(self, id: str, queue: Queue[OperatorMessage]):
        self.id = id
        self.queue = queue

    def report_progress(self, progress: float):
        self.queue.put(OperatorMessage(self.id, OperatorMessage.Type.report_progress, progress))

    def log(self, s):
        self.queue.put(OperatorMessage(self.id, OperatorMessage.Type.log, s))
