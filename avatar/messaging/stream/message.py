from typing import Union, Iterable, Any

try:
    from typing import Self
except:
    Self = 'IMessage'

from dataclasses import dataclass, field
from copy import copy
from uuid import uuid4
from datetime import datetime



def _new_id():
    return str(uuid4())


@dataclass
class Envelop:
    id: str = field(default_factory=_new_id)
    reply_to: str|None = None
    confirmation_for: tuple[str,...]|None = None
    timestamp: datetime|None = field(default_factory=datetime.now)
    publisher: str|None = None
    confirmation_stack: tuple[str,...]|None = field(default_factory=tuple)

    def extend_confirmation_stack(self, value: str|None = None):
        first = (value,) if value is not None else ()
        second = self.confirmation_stack if self.confirmation_stack is not None else ()
        return first + second


class IMessage:
    @property
    def envelop(self) -> Envelop:
        if not hasattr(self, '_envelop'):
            self._envelop = Envelop()
        if self._envelop is None:
            self._envelop = Envelop()
        return self._envelop

    def as_reply_to(self, message: Union['IMessage', str]) -> Self:
        if isinstance(message, IMessage):
            message = message.envelop.id
        elif isinstance(message, str):
            pass
        else:
            raise ValueError(f"Expected str or IMessage, but was {type(message)}")
        self.envelop.reply_to = message
        return self

    def as_confirmation_for(self, message: Union['IMessage', str, Iterable[str]]) -> Self:
        if isinstance(message, IMessage):
            confirmation_id = message.envelop.extend_confirmation_stack(message.envelop.id)
        elif isinstance(message, str):
            confirmation_id = (message,)
        else:
            try:
                confirmation_id = tuple(message)
            except:
                raise ValueError("Envelop must be IMessage or str (with message's id), or iterable of such strings")
            for c in confirmation_id:
                if not isinstance(c, str):
                    raise ValueError("Each element in the confirmation must be a str")
        self.envelop.confirmation_for = confirmation_id
        return self

    def as_propagation_confirmation_to(self, message: 'IMessage') -> Self:
        self.envelop.confirmation_stack = message.envelop.extend_confirmation_stack(message.envelop.id)
        return self

    def is_confirmation_of(self, message: Union['IMessage', str]):
        if self.envelop.confirmation_for is None:
            return False
        if isinstance(message, IMessage):
            message = message.envelop.id
        elif isinstance(message, str):
            pass
        else:
            raise ValueError("message must be IMessage or its id")
        return message in self.envelop.confirmation_for


    def as_from_publisher(self, publisher: str) -> Self:
        self.envelop.publisher = publisher
        return self

    def with_new_envelop(self) -> Self:
        result = copy(self)
        result._envelop = None
        return result

    def ensure_envelop(self) -> Self:
        _ = self.envelop
        return self

    def error_on_this(self, error: str|None = None) -> 'Confirmation':
        return Confirmation(error = error).as_confirmation_for(self).as_reply_to(self)

    def result_on_this(self, result: Any) -> 'Confirmation':
        return Confirmation(result = result).as_confirmation_for(self).as_reply_to(self)

    def confirm_this(self) -> 'Confirmation':
        return Confirmation(confirmation_details=str(self)).as_confirmation_for(self).as_reply_to(self)



@dataclass
class Confirmation(IMessage):
    result: Any = None
    error: str|None = None
    confirmation_details: str|None = None

