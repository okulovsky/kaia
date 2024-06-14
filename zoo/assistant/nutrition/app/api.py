from kaia.infra.marshalling_api import MarshallingEndpoint
from dataclasses import dataclass
from .database import ReferenceIntake, FoodUnit


class Endpoints:
    check_record = MarshallingEndpoint('/check_record')
    add_record = MarshallingEndpoint('/add_record')
    lookup_reference_intake = MarshallingEndpoint('/lookup_reference_intake')
    add_reference_intake = MarshallingEndpoint('/add_reference_intake')
    add_unit = MarshallingEndpoint('/add_unit')
    statistics = MarshallingEndpoint('/stats', 'GET')
    add_weight_measurement = MarshallingEndpoint('/add_weight_measurement', 'GET')



@dataclass
class RecordRequest:
    food: str
    amount: int
    unit: str|None
    username: str


@dataclass
class RecordReply:
    food_not_found: bool
    unit_not_found: bool

    def has_follow_up(self):
        return self.food_not_found or self.unit_not_found


class Api:
    def __init__(self, address: str):
        self.caller = MarshallingEndpoint.Caller(address)

    def check_record(self, request: RecordRequest) -> RecordReply:
        return self.caller.call(Endpoints.check_record, request)

    def add_record(self, request: RecordRequest):
        return self.caller.call(Endpoints.add_record, request)

    def lookup_reference_intake(self, food: str) -> ReferenceIntake:
        return self.caller.call(Endpoints.lookup_reference_intake, food)

    def add_reference_intake(self, intake: ReferenceIntake):
        return self.caller.call(Endpoints.add_reference_intake, intake)

    def add_unit(self, unit: FoodUnit):
        return self.caller.call(Endpoints.add_unit, unit)

    def add_weight_measurement(self, username: str, weight: float):
        return self.caller.call(Endpoints.add_weight_measurement, username, weight)












