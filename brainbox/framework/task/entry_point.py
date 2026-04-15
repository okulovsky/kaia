from .task import BrainBoxTaskOptionals
from foundation_kaia.marshalling import Signature, JSON, Serializer
from foundation_kaia.marshalling.reflector import DeclaredType
from foundation_kaia.marshalling import ENDPOINT_ATTR, SERVICE_ATTR
from typing import Generic, TypeVar, Callable
from .task_builder import TaskBuilder, TaskBuilderSignature
from ..common import IEntryPoint

T = TypeVar('T', bound=TaskBuilder)

def _parse_signatures(dt: DeclaredType, decider_name: str, ordering_token: list[str], service_only: bool = True) -> dict[str, TaskBuilderSignature]:
    argument_to_ordering_token_position = {v: e for e, v in enumerate(ordering_token)}
    signatures: dict[str, TaskBuilderSignature] = {}

    for mro_elem in dt.mro:
        if mro_elem.type is object:
            continue
        if service_only and SERVICE_ATTR not in mro_elem.type.__dict__:
            continue
        for name, member in vars(mro_elem.type).items():
            if name in signatures or name.startswith('_') or not callable(member):
                continue
            if service_only and not hasattr(member, ENDPOINT_ATTR):
                continue
            sig = Signature.parse(member, owner=mro_elem.type, type_map=mro_elem.type_map)
            signatures[name] = TaskBuilderSignature(decider_name, argument_to_ordering_token_position, sig)

    return signatures


def _parse_signatures_and_ctor(obj, ordering_token: list[str]):
    my_dt = DeclaredType.parse(type(obj))
    entry_point_elem = my_dt.find_type(EntryPoint)
    task_builder_type = entry_point_elem.type_map[T]
    tb_dt = DeclaredType.parse(task_builder_type)

    decider_name = type(obj).__name__.replace('EntryPoint', '')
    signatures = _parse_signatures(tb_dt, decider_name, ordering_token, service_only=True)

    return signatures, tb_dt.create_instance

class EntryPoint(IEntryPoint, Generic[T]):
    def __init__(self):
        sig, ctor = _parse_signatures_and_ctor(self, list(self.get_ordering_token()))
        self._signatures: dict[str, TaskBuilderSignature] = sig
        self._ctor: Callable[[], T] = ctor

    def new_task(self, *, id: str|None = None, parameter: str|None = None, batch: str|None = None, info: JSON = None) -> T:
        instance = self._ctor()
        instance._signatures = self._signatures
        instance._optionals = BrainBoxTaskOptionals(
            id,
            parameter,
            batch,
            info
        )
        instance._after_others = []
        return instance

    def get_ordering_token(self) -> tuple[str,...]:
        return ()