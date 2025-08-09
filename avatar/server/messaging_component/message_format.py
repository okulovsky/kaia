from typing import Any
from ...messaging import IMessage, Envelop
from .format import Format
from typing import *
import importlib
from dataclasses import dataclass


def get_type_by_full_name(full_name: str) -> Type[Any]:
    module_name, type_name = full_name.rsplit('/')
    module = importlib.import_module(module_name)
    try:
        return getattr(module, type_name)
    except AttributeError:
        raise ImportError(f"Module '{module_name}' has no attribute '{type_name}'")

def get_full_name_by_type(_type: Type) -> str:
    return _type.__module__ + '/' + _type.__qualname__


@dataclass
class GenericMessage(IMessage):
    payload: Any
    message_type: str = ''



class MessageFormat:
    @staticmethod
    def to_json(message: IMessage, session: str):
        return dict(
            message_type = get_full_name_by_type(type(message)),
            session = session,
            envelop = Format.to_json(message.envelop, type(message.envelop)),
            payload = Format.to_json(message, type(message))
        )

    @staticmethod
    def from_json(json):
        message_type = json['message_type']
        payload = json['payload']
        try:
            _type = get_type_by_full_name(message_type)
            message = Format.from_json(payload, _type)
        except:
            message = GenericMessage(payload, message_type)

        envelop: Envelop = Format.from_json(json['envelop'], Envelop)
        if envelop.timestamp is not None and envelop.timestamp.tzinfo is not None:
            envelop.timestamp = envelop.timestamp.astimezone().replace(tzinfo=None)
        message._envelop = envelop
        return message
