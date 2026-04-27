import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
import requests


def _new_id() -> str:
    return str(uuid.uuid4())

@dataclass
class Envelop:
    id: str = field(default_factory=_new_id)
    reply_to: Optional[str] = None
    confirmation_for: Optional[list[str]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    publisher: Optional[str] = None
    confirmation_stack: list[str] = field(default_factory=list)


@dataclass
class Message:
    message_type: str
    envelop: Envelop = field(default_factory=Envelop)
    payload: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(raw: dict) -> 'Message':
        return Message(
            message_type=raw['content_type'],
            envelop=Envelop(**raw['envelop']),
            payload=raw.get('content') or {},
        )


class SimpleAvatarClient:
    def __init__(self, base_url: str, session: str = 'default', allowed_types: Optional[list[str]] = None):
        self.base_url = base_url.rstrip('/')
        self.session = session
        self.allowed_types = allowed_types
        self.last_id: Optional[str] = None

    def push(self, msg: Message) -> None:
        url = f'{self.base_url}/messaging/put'
        msg.envelop.publisher = 'console'
        body = {
            'message': {
                'session': self.session,
                'content_type': msg.message_type,
                'envelop': msg.envelop.__dict__,
                'content': msg.payload,
            }
        }
        resp = requests.post(url, json=body)
        resp.raise_for_status()

    def pull(self, timeout_in_seconds: Optional[float] = None, max_messages: Optional[int] = None) -> list[Message]:
        url = f'{self.base_url}/messaging/get/{requests.utils.quote(self.session, safe="")}'
        params = {}
        if self.last_id is not None:
            params['last_id'] = self.last_id
        if max_messages is not None:
            params['max_messages'] = str(max_messages)
        if timeout_in_seconds is not None:
            params['timeout_in_seconds'] = str(timeout_in_seconds)

        resp = requests.post(url, params=params, json={'allowed_types': self.allowed_types})
        resp.raise_for_status()

        data = resp.json()
        messages = [Message.from_dict(raw) for raw in data['messages']]

        if messages:
            self.last_id = messages[-1].envelop.id

        return messages

    def tail(self, count: int|None = None) -> list[Message]:
        url = f'{self.base_url}/messaging/tail/{requests.utils.quote(self.session, safe="")}'
        params = {}
        if count is not None:
            params['count'] = str(count)
        resp = requests.post(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return [Message.from_dict(raw) for raw in data['messages']]

    def set_last_id(self, last_id: Optional[str]) -> None:
        self.last_id = last_id

    def scroll_to_end(self) -> None:
        messages = self.tail(1)
        if messages:
            self.last_id = messages[-1].envelop.id
        else:
            self.last_id = None
