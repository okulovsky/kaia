from ...controllers import ControllerRegistry
from .operator_state import OperatorState
from .operator_log import OperatorLog
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from .job import Job
import traceback
from abc import ABC, abstractmethod
from .trackable_session_factory import TrackableSessionFactory
from .job_for_planner import JobForPlanner
from ...common import Locator, Loc

class SessionFactory:
    def __init__(self, engine):
        self._engine = engine

    def __call__(self):
        return Session(self._engine)


class Core:
    def __init__(self,
                 engine: Engine,
                 registry: ControllerRegistry,
                 locator: Locator = Loc,
                 debug_output: bool = False,
                 ):
        self._engine = engine
        self.new_session = SessionFactory(self._engine)# TrackableSessionFactory(self._engine, Core.job_to_id)
        self.registry = registry
        self.locator = locator
        self.operator_states: dict[str, OperatorState] = dict()
        self.operator_log: OperatorLog = OperatorLog(debug_output)
        self.jobs_for_planner: tuple[JobForPlanner,...]|None = None

    @staticmethod
    def job_to_id(job: Job):
        return job.id

    def get_job_by_id(self, session: Session, id: str):
        return session.scalar(select(Job).where(Job.id == id))

    def close_job(self, session: Session, job: Job, custom_message: str):
        self.operator_log.task(job.id).event(custom_message)
        if custom_message is None:
            custom_message = traceback.format_exc()
        job.finished = True
        job.success = False
        job.error = custom_message


class ICoreAction(ABC):
    @abstractmethod
    def apply(self, core: Core):
        pass