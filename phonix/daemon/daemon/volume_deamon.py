import time
from avatar.daemon import VolumeEvent
from avatar.messaging import StreamClient
from .volume import VolumeController


class VolumeDeamon:
    def __init__(self,
                 client: StreamClient,
                 controller: VolumeController,
                 rate_in_seconds: float
                 ):
        self.client = client
        self.controller = controller
        self.rate_in_seconds = rate_in_seconds
        self.reported_volume = None

    def run(self):
        if self.controller is None:
            return
        while True:
            time.sleep(self.rate_in_seconds)
            volume = self.controller.get()
            if self.reported_volume is None or self.reported_volume != volume:
                self.reported_volume = volume
                self.client.put(VolumeEvent(volume))


