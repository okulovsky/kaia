from avatar.messaging import StreamClient
from avatar.daemon import NarrationService, State

class KaiaContext:
    def __init__(self, client: StreamClient):
        self._client = client

    def get_client(self):
        return self._client.clone()

    def get_state(self) -> State:
        return self.get_client().run_synchronously(NarrationService.StateRequest(), State)
