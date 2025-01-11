from dataclasses import dataclass, field
from .decider_instance_key import DeciderInstanceKey
from datetime import datetime
from queue import Queue
from .job import Job
from .operator_message import OperatorMessage
from .operator_log import OperatorLog
from ...controllers.controller import IController
from ...common import IDecider
from threading import Thread

@dataclass
class OperatorStateForPlanner:
    instance_id: str
    key: DeciderInstanceKey
    busy: bool
    not_busy_since: datetime|None


@dataclass
class OperatorState:
    key: DeciderInstanceKey
    controller: IController
    controller_run_instance_id: str
    api: IDecider
    logger: OperatorLog = field(default_factory=OperatorLog)
    operator_thread: Thread|None = None
    exit_request: bool = False
    busy: bool = False
    not_busy_since: datetime|None = None
    jobs_queue: Queue[Job] = field(default_factory=Queue)
    results_queue: Queue[OperatorMessage] = field(default_factory=Queue)





