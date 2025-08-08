from dataclasses import dataclass
from brainbox import BrainBox
from brainbox.framework import ControllersSetup
from .app import KaiaApp, IAppInitializer
from avatar.messaging import AvatarProcessor
from avatar import services as s
from avatar.services.common import content_manager as cm, AvatarService
import inspect
from brainbox.deciders import Piper, RhasspyKaldi, Whisper, Resemblyzer
from pathlib import Path
from kaia.assistant import KaiaAssistant


characters =  ('Ocean', 'Mountain', 'Meadow', 'Forest')

class DemoDubTaskFactory(s.TTSService.TaskFactory):
    def create_task(self, s: str, info: s.TextInfo) -> BrainBox.ITask:
        return BrainBox.Task.call(Piper).voiceover(s, info.language)

def _speaker_to_image_url(speaker):
    return f'/static/unknown.png'


@dataclass
class AvatarServiceSetup:
    service: AvatarService
    is_asynchronous: bool = False


@dataclass
class AvatarProcessorAppSettings(IAppInitializer):
    timer_event_span_in_seconds: float = 1
    initialization_event_at_startup: bool = True
    error_events: bool = True

    def create_brainbox_service(self, app: KaiaApp, state: s.State):
        bbox = s.BrainBoxService(
            app.brainbox_api,
            ControllersSetup((
                 ControllersSetup.Instance(RhasspyKaldi),
                 ControllersSetup.Instance(Whisper, None, 'base'),
                 ControllersSetup.Instance(Piper),
                 ControllersSetup.Instance(Resemblyzer),
            )))
        return AvatarServiceSetup(
            bbox,
            True
        )


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

    def create_stt_service(self, app: KaiaApp, state: s.State):
        return s.STTService(
            s.RhasspyRecognitionSetup(KaiaAssistant.RHASSPY_MAIN_MODEL_NAME)
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
        return s.TTSService(
            DemoDubTaskFactory()
        )

    def create_volume_control_service(self, app: KaiaApp, state: s.State):
        return s.VolumeControlService()

    def create_chat_service(self, app: KaiaApp, state: s.State):
        return s.ChatService(state, _speaker_to_image_url)

    def create_sound_event_to_stt_command(self, app: KaiaApp, state: s.State):
        return s.STTIntegrationService(state)

    def create_text_command_to_tts_command(self, app: KaiaApp, state: s.State):
        return s.TTSIntegrationService()

    def new_state(self):
        return s.State(character=characters[0], language='en')

    def bind_app(self, app: KaiaApp):
        proc = AvatarProcessor(
            app.create_avatar_client(),
            self.timer_event_span_in_seconds,
            self.error_events
        )
        state = self.new_state()

        methods = [
            member for name, member in inspect.getmembers(self, predicate=inspect.ismethod)
            if name.startswith("create_")
        ]
        for method in methods:
            service = method(app, state)

            if service is None:
                continue

            if isinstance(service, AvatarService):
                setup = AvatarServiceSetup(service)
            elif isinstance(service, AvatarServiceSetup):
                setup = service
            else:
                raise ValueError(f"Method {method.__name__} retured {type(service)} while AvatarService or AvatarServiceSetup is expected")
            if app.brainbox_api is None and setup.service.requires_brainbox():
                continue
            print(f'Binding {setup.service}')
            proc.rules.bind(setup.service, is_asyncronous=setup.is_asynchronous)

        app.avatar_processor = proc





