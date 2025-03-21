from .interface import IAvatarApi
from .server import AvatarServer, AvatarService
from brainbox.framework.common.marshalling import Api, bind_to_api, TestApi
from .state_change import StateChange

@bind_to_api(AvatarService)
class AvatarApi(Api, IAvatarApi):
    def __init__(self, address: str):
        super().__init__(address)

    class Test(TestApi['AvatarApi']):
        def __init__(self, settings):
            super().__init__(AvatarApi, AvatarServer(settings))

    def push_state(self, change):
        return StateChange(self, change)