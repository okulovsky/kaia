from foundation_kaia.marshalling_2 import service, endpoint
from .avatar_message import AvatarMessage
from ...messaging import AvatarMessageSet

@service
class IAvatarMessagingService:
    @endpoint
    def put(self, message: AvatarMessage):
        ...

    @endpoint
    def get(self,
                 session: str,
                 last_id: str|None = None,
                 timeout_in_seconds: float|None = None,
                 max_messages: int|None = None,
                 allowed_types: list[str]|None = None,
                 ) -> AvatarMessageSet[AvatarMessage]:
        pass

    @endpoint
    def tail(self,
                  session: str,
                  count: int|None = None,
                  from_timestamp=None,
                  ) -> AvatarMessageSet[AvatarMessage]:
        pass

