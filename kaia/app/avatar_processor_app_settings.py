from dataclasses import dataclass
from avatar.services import TextInfo
from brainbox import BrainBox
from .app import KaiaApp, IAppInitializer
from avatar.messaging import AvatarProcessor, IMessage
from avatar import services as s
from avatar.services.common import content_manager as cm, AvatarService
import inspect
from brainbox.deciders import Piper
from pathlib import Path


characters =  ('Ocean', 'Mountain', 'Meadow', 'Forest')

class DemoDubTaskFactory(s.VoiceoverService.TaskFactory):
    def create_task(self, s: str, info: TextInfo) -> BrainBox.ITask:
        return BrainBox.Task.call(Piper).voiceover(s, info.language)

def _speaker_to_image_url(speaker):
    return f'/static/unknown.png'

@dataclass
class AvatarProcessorAppSettings(IAppInitializer):
    timer_event_span_in_seconds: float = 1
    initialization_event_at_startup: bool = True

    def create_brainbox_service(self, app: KaiaApp, state: s.State):
        return s.BrainBoxService(app.brainbox_api)


    def create_image_service(self, app:KaiaApp, state: s.State):
        image_strategy = cm.SequentialStrategy(
            cm.WeightedStrategy(
                cm.WeightedStrategy.Item(cm.GoodContentStrategy(), 0.3),
                cm.WeightedStrategy.Item(cm.NewContentStrategy(), 0.7),
            ),
            cm.NewContentStrategy(),
            cm.AnyContentStrategy(),
        )
        image_manager = cm.MediaLibraryManager(
            Path(__file__).parent/'files/image_library.zip',
            Path(__file__).parent / 'files/image_library_feedback.json',
            image_strategy,
        )
        return s.ImageService(
            state,
            image_manager,
        )

    def create_narration_service(self, app: KaiaApp, state: s.State):
        return s.NarrationService(
            state,
            characters,
            None,
            s.TextCommand("Hello! Nice to see you!"),
            60
        )

    def create_state_to_utterances_application(self, app: KaiaApp, state: s.State):
        return s.StateToUtterancesApplicationService(state)

    def create_voiceover_service(self, app: KaiaApp, state: s.State):
        return s.VoiceoverService(
            DemoDubTaskFactory()
        )

    def create_volume_control_service(self, app: KaiaApp, state: s.State):
        return s.VolumeControlService()

    def create_chat_service(self, app: KaiaApp, state: s.State):
        return s.ChatService(state, _speaker_to_image_url)



    def bind_app(self, app: KaiaApp):
        proc = AvatarProcessor(
            app.avatar_stream.create_client(),
            self.timer_event_span_in_seconds,
            self.initialization_event_at_startup
        )
        state = s.State()

        methods = [
            member for name, member in inspect.getmembers(self, predicate=inspect.ismethod)
            if name.startswith("create_")
        ]
        for method in methods:
            service = method(app, state)
            if service is None:
                continue
            if not isinstance(service, AvatarService):
                raise ValueError(f"Method {method.__name__} retured {type(service)} while AvatarService is expected")
            if app.brainbox_api is None and service.requires_brainbox():
                continue
            proc.rules.bind(service)

        app.avatar_processor = proc





