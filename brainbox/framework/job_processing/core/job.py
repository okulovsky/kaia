from typing import *
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import JSON, PickleType, func
from datetime import datetime
from .decider_instance_key import DeciderInstanceKey

BrainBoxBase = declarative_base()

class Job(BrainBoxBase):
    __tablename__ = "brain_box_jobs"

    id: Mapped[str] = mapped_column(primary_key=True)
    decider: Mapped[str] = mapped_column()
    decider_parameter: Mapped[str] = mapped_column(nullable=True)
    method: Mapped[str] = mapped_column(nullable=True)
    arguments: Mapped[Any] = mapped_column(type_ = PickleType)
    info: Mapped[Any] = mapped_column(type_= PickleType, nullable=True)
    batch: Mapped[str] = mapped_column()
    ordering_token: Mapped[str] = mapped_column(nullable=True)

    received_timestamp: Mapped[datetime] = mapped_column()

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

    last_update_timestamp: Mapped[datetime] = mapped_column(
        default=func.strftime('%Y-%m-%d %H:%M:%f', 'now'),
        onupdate=func.strftime('%Y-%m-%d %H:%M:%f', 'now')
    )


    def get_this_and_dependency_ids(self):
        result = [self.id]
        if self.dependencies is not None:
            for key in sorted(self.dependencies):
                result.append(self.dependencies[key])
        return result

    def get_key(self):
        return DeciderInstanceKey(self.decider, self.decider_parameter)

    def set_defaults(self, now: datetime|None = None):
        if now is None:
            now = datetime.now()
        self.received_timestamp = now
        self.batch = self.batch if self.batch is not None else self.id
        self.has_dependencies = self.dependencies is not None
        return self

