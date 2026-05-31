from .avatar_message import AvatarMessage
from ...messaging.core import AvatarMessageSet, IMessage
from .interface import IAvatarMessagingService
from typing import Any
from .queue import Queue
from datetime import datetime
from time import monotonic, sleep
from foundation_kaia.marshalling import TypeTools
from pathlib import Path
from .stasher import Stasher

class AvatarMessagingService(IAvatarMessagingService):
    def __init__(self,
                 aliases: dict[str, type]|None = None,
                 ttl_in_seconds: int|None = 60*60,
                 starting_messages: dict[str,tuple[IMessage,...]]|None = None,
                 messages_log_folder: Path|None = None
                 ):
        self.ttl_in_seconds = ttl_in_seconds
        self.aliases = aliases
        self.queues: dict[str, Any] = {}
        if messages_log_folder is not None:
            self.stasher = Stasher(messages_log_folder)
        else:
            self.stasher = None

        from .message_repository import AvatarMessageRepository
        if starting_messages is not None:
            for session, messages in starting_messages.items():
                for message in messages:
                    avatar_message = AvatarMessageRepository._serialize(session, message)
                    self.put(avatar_message)

    def _ensure_full_type(self, t: str):
        if self.aliases is not None and t in self.aliases:
            return TypeTools.type_to_full_name(self.aliases[t])
        return t


    def put(self, message: AvatarMessage):
        if self.stasher is not None:
            self.stasher.stash(message)
        if message.session not in self.queues:
            self.queues[message.session] = Queue(self.ttl_in_seconds)
        message.content_type = self._ensure_full_type(message.content_type)
        message.envelop.timestamp = datetime.now()
        self.queues[message.session].add(message)

    def get(self,
                 session: str,
                 last_id: str|None = None,
                 timeout_in_seconds: float|None = None,
                 max_messages: int | None = None,
                 allowed_types: list[str]|None = None,
                 ) -> AvatarMessageSet[AvatarMessage]:
        if not allowed_types:
            allowed_types = None

        if session not in self.queues:
            return AvatarMessageSet(last_id is not None, True, [])
        queue = self.queues[session]

        if last_id is None:
            index = -1
            last_id_not_found = False
        else:
            idx = queue.get_index(last_id)
            if idx is None:
                index = -1
                last_id_not_found = True
            else:
                index = idx
                last_id_not_found = False

        start_index = max(index + 1, queue.first_index)

        begin_time = monotonic()
        while True:
            messages = queue.get_from(start_index)
            if messages:
                if allowed_types is not None:
                    messages = [m for m in messages if any(m.content_type.endswith(t) for t in allowed_types)]
                if messages:
                    break
            if timeout_in_seconds is not None and monotonic() - begin_time > timeout_in_seconds:
                return AvatarMessageSet(last_id_not_found, False, [])
            sleep(0.01)

        if max_messages is not None:
            messages = messages[:max_messages]
        return AvatarMessageSet(last_id_not_found, False, messages)

    def tail(self,
                  session: str,
                  count: int|None = None,
                  allowed_types: list[str] | None = None,
                  from_timestamp=None,
                  ) -> AvatarMessageSet[AvatarMessage]:
        if not allowed_types:
            allowed_types = None

        if session not in self.queues:
            return AvatarMessageSet(True, True, [])
        queue = self.queues[session]

        if from_timestamp is not None:
            start = queue.find_index_from_timestamp(from_timestamp)
            messages = queue.get_from(start)
        elif count is not None:
            if allowed_types is not None:
                messages = queue.get_from(queue.first_index)
                messages = [m for m in messages if any(m.content_type.endswith(t) for t in allowed_types)]
                messages = messages[-count:]
            else:
                messages = queue.get_from(queue.first_index)[-count:]
        else:
            messages = queue.get_from(queue.first_index)

        if allowed_types is not None and from_timestamp is not None:
            messages = [m for m in messages if any(m.content_type.endswith(t) for t in allowed_types)]

        return AvatarMessageSet(True, False, messages)










