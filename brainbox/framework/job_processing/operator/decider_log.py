from ...common import ApiCallback
from ..core import OperatorMessage, CommandQueue, OperatorLog
from ..main_loop.task_finished_action import TaskFinishedAction
from ..main_loop.task_update_reminder import TaskUpdateReminder
from queue import Queue

class DeciderLogger(ApiCallback):
    def __init__(self, id: str, queue: Queue[OperatorMessage], command_queue: CommandQueue, operator_log: OperatorLog):
        self.id = id
        self.queue = queue
        self.command_queue = command_queue
        self.operator_log = operator_log

    def report_progress(self, progress: float):
        self.queue.put(OperatorMessage(self.id, OperatorMessage.Type.report_progress, progress))
        self.command_queue.put(TaskUpdateReminder())

    def log(self, s):
        self.queue.put(OperatorMessage(self.id, OperatorMessage.Type.log, s))
        self.command_queue.put(TaskUpdateReminder())

    def report_responding(self, filename: str):
        self.queue.put(OperatorMessage(self.id, OperatorMessage.Type.responding, filename))
        self.operator_log.task(self.id).event("Responding")
        self.command_queue.put_action(TaskFinishedAction())
