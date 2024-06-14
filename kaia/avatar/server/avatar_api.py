from typing import *
from ..dub.core import Utterance, Template
from .avatar_server import AvatarEndpoints, AvatarWebServer, AvatarSettings
from ..narrator import INarrator
from .dubbing_service import IDubbingService
from .image_service import IImageService
from ...infra import MarshallingEndpoint
from ...eaglesong.core import Audio, Image
from ...infra.app import KaiaApp, SubprocessRunner
from ...infra import Loc

class AvatarAPI:
    def __init__(self,
                 address: str):
        self.caller = MarshallingEndpoint.Caller(address)

    def dub_utterance(self, utterance: Utterance) -> Audio:
        return self.caller.call(AvatarEndpoints.dub_utterance, utterance)

    def dub_string(self, s: str) -> Audio:
        return self.caller.call(AvatarEndpoints.dub_string, s)

    def image_get(self, empty_image_if_none = True) -> Optional[Image]:
        image = self.caller.call(AvatarEndpoints.image_get)
        if image is None and empty_image_if_none:
            return self.empty_image()
        return image

    def empty_image(self):
        return _empty_image

    def image_report(self, report: str) -> None:
        return self.caller.call(AvatarEndpoints.image_report, report)

    def state_change(self, change: dict[str, Any]) -> None:
        return self.caller.call(AvatarEndpoints.state_change, change)

    def state_get(self) -> dict[str, Any]:
        return self.caller.call(AvatarEndpoints.state_get)


class AvatarTestApi:
    def __init__(self,
                 settings: AvatarSettings,
                 narrator: INarrator,
                 dubbing_service: IDubbingService,
                 image_service: IImageService):
        self.settings = settings
        self.narrator = narrator
        self.dubbing_service = dubbing_service
        self.image_service = image_service

    def __enter__(self):
        service = AvatarWebServer(
            AvatarSettings(),
            self.narrator,
            self.dubbing_service,
            self.image_service,
            Loc.temp_folder/'avatar_service_error_path'
        )
        self.app = KaiaApp()
        self.app.add_runner(SubprocessRunner(service, 5))
        self.app.run_services_only()

        api = AvatarAPI(f'127.0.0.1:{self.settings.port}')
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app.exit()


_empty_image = Image(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82', None, None)
