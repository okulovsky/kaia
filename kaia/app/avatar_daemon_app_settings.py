from typing import Callable, Any
from dataclasses import dataclass, field
from brainbox import BrainBox
from brainbox.framework import ControllersSetup
from .app import KaiaApp, IAppInitializer
from avatar.messaging import AvatarDaemon
from avatar import daemon as s
from avatar.daemon.common import content_manager as cm, AvatarService
import inspect
from brainbox.deciders import Piper, RhasspyKaldi, Whisper, Resemblyzer
from pathlib import Path
from kaia.assistant import KaiaAssistant
from yo_fluq import FileIO

class DemoDubTaskFactory(s.TTSService.TaskFactory):
    def create_task(self, s: str, info: s.TextInfo) -> BrainBox.ITask:
        return BrainBox.Task.call(Piper).voiceover(s, info.language)

def _speaker_to_image_url(speaker):
    return f'/static/unknown.png'


def _default_greetings():
    return s.TextCommand("Hello! Nice to see you!")

CHARACTERS = ('Ocean', 'Mountain', 'Meadow', 'Forest')

@dataclass
class AvatarDaemonAppSettings(IAppInitializer):
    timer_event_span_in_seconds: float = 1
    error_events: bool = True
    characters: tuple[str,...] = CHARACTERS
    activity: tuple[str,...] = ('morning', 'day', 'night')  # doesn't affect anything, only needed for testing
    dub_task_factory: s.TTSService.TaskFactory = field(default_factory=DemoDubTaskFactory)
    speaker_to_image_url: Callable[[str], str] = _speaker_to_image_url
    greetings_command: Any = field(default_factory=_default_greetings)
    image_library_path: Path = Path(__file__).parent/'files/image_library.zip'
    image_library_feedback_path: Path = Path(__file__).parent / 'files/image_library_feedback.json'
    paraphrases_path: Path|None = None
    paraphrases_feedback_path: Path = None
    initialize_volume: bool = False
    report_to_session: str|None = None



    def create_brainbox_service(self, app: KaiaApp, state: s.State):
        bbox = s.BrainBoxService(
            app.brainbox_api,
            ControllersSetup((
                 ControllersSetup.Instance(RhasspyKaldi),
                 ControllersSetup.Instance(Whisper, None, 'base'),
                 ControllersSetup.Instance(Piper),
                 ControllersSetup.Instance(Resemblyzer),
            )))
        bbox.binding_settings.asynchronous(True)
        return bbox


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
            self.image_library_path,
            self.image_library_feedback_path,
            image_strategy,
        )
        return s.ImageService(
            state,
            app.avatar_api,
            image_manager,
        )

    def create_stt_service(self, app: KaiaApp, state: s.State):
        return s.STTService(
            s.RhasspyRecognitionSetup(KaiaAssistant.RHASSPY_MAIN_MODEL_NAME)
        )

    def create_narration_service(self, app: KaiaApp, state: s.State):
        return s.NarrationService(
            state,
            self.characters,
            self.activity,
            self.greetings_command,
            30*60
        )

    def create_state_to_utterances_application(self, app: KaiaApp, state: s.State):
        return s.StateToUtterancesApplicationService(state)

    def create_voiceover_service(self, app: KaiaApp, state: s.State):
        return s.TTSService(
            self.dub_task_factory
        )

    def create_volume_control_service(self, app: KaiaApp, state: s.State):
        return s.VolumeControlService(initialize_volume=self.initialize_volume)

    def create_paraphrase_service(self, app: KaiaApp, state: s.State):
        manager = None
        if self.paraphrases_path is not None:
            paraphrase_strategy = cm.SequentialStrategy(
                cm.NewContentStrategy(),
                cm.AnyContentStrategy()
            )

            manager = cm.ContentManager(
                cm.DataClassDataProvider(FileIO.read_pickle(self.paraphrases_path)),
                app.working_folder / 'avatar/paraphrases-feedback.json',
                paraphrase_strategy,
            )
        service = s.ParaphraseService(state, manager)
        service.binding_settings.bind_type(s.PlayableTextMessage).to_all_except(s.ParaphraseService)
        return service

    def create_chat_service(self, app: KaiaApp, state: s.State):
        service = s.ChatService(state, self.speaker_to_image_url)
        service.binding_settings.bind_type(s.PlayableTextMessage).to(s.ParaphraseService)
        return service

    def create_text_command_to_tts_command(self, app: KaiaApp, state: s.State):
        service = s.TTSIntegrationService()
        service.binding_settings.bind_type(s.PlayableTextMessage).to(s.ParaphraseService)
        return service


    def create_sound_event_to_stt_command(self, app: KaiaApp, state: s.State):
        return s.STTIntegrationService(state)



    def create_autoconfirm(self, app: KaiaApp, state: s.State):
        if app.brainbox_api is None:
            return s.MockVoiceoverService()

    def create_sound_command_unblocker(self, app: KaiaApp, state: s.State):
        return s.SoundPlayUnblockerService()

    def new_state(self):
        return s.State(character=self.characters[0], language='en')

    def bind_app(self, app: KaiaApp):
        reporting_stream = None
        if self.report_to_session is not None:
            reporting_stream = app.avatar_api.create_messaging_stream(self.report_to_session).create_client().as_asyncronous()

        proc = AvatarDaemon(
            app.create_avatar_client(),
            self.timer_event_span_in_seconds,
            self.error_events,
            reporting_stream
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

            if app.brainbox_api is None and isinstance(service, AvatarService) and service.requires_brainbox():
                continue
            print(f'Binding {service}')
            proc.rules.bind(service)

        app.avatar_processor = proc





