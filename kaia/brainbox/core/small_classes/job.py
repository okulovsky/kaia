from typing import *
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import JSON, PickleType
from datetime import datetime
from .task import BrainBoxTask
from .decider_instance_dto import DeciderInstanceSpec


BrainBoxBase = declarative_base()

class BrainBoxJob(BrainBoxBase):
    __tablename__ = "brain_box_jobs"

    id: Mapped[str] = mapped_column(primary_key=True)
    decider: Mapped[str] = mapped_column()
    decider_parameters: Mapped[str] = mapped_column(nullable=True)
    method: Mapped[str] = mapped_column(nullable=True)
    arguments: Mapped[Any] = mapped_column(type_ = PickleType)
    back_track: Mapped[Any] = mapped_column(type_= JSON, nullable=True)
    received_timestamp: Mapped[datetime] = mapped_column()
    batch: Mapped[str] = mapped_column(nullable=True)

    dependencies: Mapped[Optional[Dict[str, str]]] = mapped_column(type_=JSON, default = None)
    has_dependencies: Mapped[bool] = mapped_column(nullable=False)
    ready: Mapped[bool] = mapped_column(default=False)
    ready_timestamp: Mapped[datetime] = mapped_column(nullable=True)

    assigned: Mapped[bool] = mapped_column(default=False)
    assigned_timestamp: Mapped[datetime] = mapped_column(nullable=True)

    accepted: Mapped[bool] = mapped_column(default=False)
    accepted_timestamp: Mapped[datetime] = mapped_column(nullable=True)

    progress: Mapped[Optional[float]] = mapped_column(nullable=True, default=None)
    log: Mapped[Optional[List[str]]] = mapped_column(nullable=True, default=None, type_ = JSON)

    finished: Mapped[bool] = mapped_column(default=False)
    finished_timestamp: Mapped[datetime] = mapped_column(nullable=True)
    success: Mapped[bool] = mapped_column(default=False)
    result: Mapped[Any] = mapped_column(type_ = PickleType, nullable=True, default=None)
    error: Mapped[str] = mapped_column(nullable=True, default=None)


    def get_this_and_dependency_ids(self):
        result = [self.id]
        if self.dependencies is not None:
            for key in sorted(self.dependencies):
                result.append(self.dependencies[key])
        return result

    def get_decider_instance_spec(self):
        return DeciderInstanceSpec(self.decider, self.decider_parameters)


    @staticmethod
    def from_task(task:BrainBoxTask) -> 'BrainBoxJob':
        timestamp = datetime.now()
        return BrainBoxJob(
            id=task.id,
            decider=task.decider,
            decider_parameters = task.decider_parameters,
            method=task.decider_method,
            batch=task.batch,
            arguments=task.arguments,
            back_track=task.back_track,
            received_timestamp=timestamp,
            dependencies=task.dependencies,
            has_dependencies=task.dependencies is not None
        )

