from .api import Endpoints
from kaia.infra.marshalling_api import MarshallingEndpoint
import flask
from dataclasses import dataclass
from kaia.infra import Loc
from pathlib import Path
from sqlalchemy import create_engine, Engine, select, delete, update
from sqlalchemy.orm import Session

from .database import *
from .api import Endpoints, RecordRequest, RecordReply

class Settings:
    port: int = 9001
    db_path: Path = Loc.data_folder/'nutrition_db'


class Server:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine: Engine|None = None


    def __call__(self):
        self.engine = create_engine('sqlite:///'+str(self.settings.db_path))
        Base.metadata.create_all(self.engine)
        self.app = flask.Flask('nutrition')
        binder = MarshallingEndpoint.Binder(self.app)
        binder.bind_all(Endpoints, self)
        self.app.run('0.0.0.0',self.settings.port)

    def check_record(self, request: RecordRequest) -> RecordReply:
        with Session(self.engine) as session:
            unit_found = len(list(session.execute(
                select(FoodUnit)
                .where( (FoodUnit.food==request.food ) & (FoodUnit.unit == request.unit))
            ))) > 0

            reference_intake_available = len(list(session.execute(
                select(ReferenceIntake)
                .where(ReferenceIntake.food == request.food)
            ))) > 0
        return RecordReply(not reference_intake_available, not unit_found)


    def add_record(self, request: RecordRequest):
        with Session(self.engine) as session:
            session.add(DiaryRecord(
                username=request.username,
                timestamp=datetime.now(),
                food=request.food,
                amount=request.amount,
                unit=request.unit
            ))
            session.commit()

    def lookup_reference_intake(self, food: str) -> ReferenceIntake:
        raise ValueError("Not implemented yet")

    def add_reference_intake(self, intake: ReferenceIntake):
        with Session(self.engine) as session:
            session.add(intake)
            session.commit()

    def add_unit(self, unit: FoodUnit):
        with Session(self.engine) as session:
            session.add(unit)
            session.commit()

    def add_weight_measurement(self, username: str, weight: float):
        with Session(self.engine) as session:
            session.add(WeightMeasurement())



