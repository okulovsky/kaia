from typing import *
from .avatar_server import AvatarEndpoints, AvatarWebServer, AvatarSettings
from .dubbing_service import TextLike, DubbingServiceOutput
from kaia.infra import MarshallingEndpoint
from kaia.eaglesong.core import Image, Audio
from kaia.infra.app import KaiaApp, SubprocessRunner


class AvatarAPI:
    def __init__(self,
                 address: str):
        self.caller = MarshallingEndpoint.Caller(address)

    def dub(self, text: TextLike) -> DubbingServiceOutput:
        return self.caller.call(AvatarEndpoints.dub, text)

    def dub_get_result(self, job_id: str) -> Audio:
        return self.caller.call(AvatarEndpoints.dub_get_result, job_id)

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
    def __init__(self, settings: AvatarSettings):
        self.settings = settings

    def __enter__(self):
        service = AvatarWebServer(self.settings)
        self.app = KaiaApp()
        self.app.add_runner(SubprocessRunner(service))
        self.app.run_services_only()

        api = AvatarAPI(f'127.0.0.1:{self.settings.port}')
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app.exit()


_empty_image = Image(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82', None, None)
