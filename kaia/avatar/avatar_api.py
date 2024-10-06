from typing import *
from .avatar_server import AvatarEndpoints, AvatarServer, AvatarSettings
from .dubbing_service import TextLike, DubbingServiceOutput
from .recognition_service import RecognitionSettings
from kaia.dub import Template, IntentsPack
from kaia.infra import MarshallingEndpoint
from kaia.eaglesong.core import Image, Audio
from kaia.infra.app import KaiaApp, SubprocessRunner
from pathlib import Path

class AvatarApi(MarshallingEndpoint.API):
    def __init__(self,
                 address: str,
                 session_id: str = 'default'
                 ):
        self.session_id = session_id
        super().__init__(address)

    def dub(self, text: TextLike) -> DubbingServiceOutput:
        return self.caller.call(AvatarEndpoints.dub, self.session_id, text)

    def dub_get_result(self, job_id: str) -> Audio:
        return self.caller.call(AvatarEndpoints.dub_get_result, job_id)

    def image_get(self, empty_image_if_none = True) -> Optional[Image]:
        image = self.caller.call(AvatarEndpoints.image_get, self.session_id)
        if image is None and empty_image_if_none:
            return self.empty_image()
        return image

    def empty_image(self):
        return _empty_image

    def image_report(self, report: str) -> None:
        return self.caller.call(AvatarEndpoints.image_report, self.session_id, report)

    def state_change(self, change: dict[str, Any]) -> None:
        return self.caller.call(AvatarEndpoints.state_change, self.session_id, change)

    def state_get(self) -> dict[str, Any]:
        return self.caller.call(AvatarEndpoints.state_get, self.session_id)

    def recognition_train(self, intents: tuple[IntentsPack,...], replies: tuple[Template,...]):
        return self.caller.call(AvatarEndpoints.recognition_train, self.session_id, intents, replies)

    def recognition_transcribe(self, file_id: str, settings: RecognitionSettings):
        return self.caller.call(AvatarEndpoints.recognition_transcribe, self.session_id, file_id, settings)

    def recognition_speaker_fix(self, actual_speaker: str):
        return self.caller.call(AvatarEndpoints.recognition_speaker_fix, self.session_id, actual_speaker)

    def recognition_speaker_train(self, media_library_path: Path):
        return self.caller.call(AvatarEndpoints.recognition_speaker_train, self.session_id,  media_library_path)

    class Test(MarshallingEndpoint.TestAPI):
        def __init__(self, settings: AvatarSettings, session_id: str = 'default'):
            self.settings = settings
            self.session_id = session_id

        def __enter__(self) -> 'AvatarApi':
            service = AvatarServer(self.settings)
            api = AvatarApi(f'127.0.0.1:{self.settings.port}', self.session_id)
            return self._prepare_service(api, service)



_empty_image = Image(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82', None, None)
