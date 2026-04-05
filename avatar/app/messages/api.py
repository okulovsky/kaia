from foundation_kaia.marshalling_2.marshalling.server.api_call import ApiCall
from .interface import IAvatarMessagingService


class AvatarMessagingApi(IAvatarMessagingService):
    def __init__(self, base_url: str):
        self._base_url = base_url
        ApiCall.define_endpoints(self, base_url, IAvatarMessagingService, 'messaging')
