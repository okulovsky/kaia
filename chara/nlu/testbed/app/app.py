import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
import requests
from grammatron import Template
from foundation_kaia.misc import Loc
from avatar.app import compile_frontend
from avatar.daemon import StreamingSTTService, STTIntegrationService, SilenceLevelService, State
from avatar.daemon.streaming_stt_service import IntentSource
from brainbox import BrainBox
from brainbox.framework import BrainBoxSetup, BrainBoxServer, BrainBoxServerSettings, BrainBoxLocations, ControllerRegistry, AlwaysOnPlanner
from brainbox.deciders import WhisperKenLM, Nemotron, Chroma, LlamaLoraSFTTrainer, LlamaLoraServer
from chara.nlu.ner_training import NerTrainingPipeline
from chara.nlu.scripts import deploy_ultimate_nlu
from kaia.app import KaiaAppSettings, AvatarDaemonAppSettings, KaiaApp
from .reporting_nlu_service import ReportingNLUService
from .testbed_service import TestbedService, TestbedChatService
from .silence_skipping_stt_service import SilenceSkippingWhisperKenLMSTTService


class Stt:
    NEMOTRON = 'nemotron'
    # Nemotron in each of LANGUAGES at once, the most confident text is taken, see StreamingSTTService
    NEMOTRON_LANGUAGES = 'nemotron-languages'
    WHISPER_KENLM = 'whisper-kenlm'
    ALL = (NEMOTRON, NEMOTRON_LANGUAGES, WHISPER_KENLM)
    LANGUAGES = ('en', 'de', 'ru')


@dataclass
class TestbedDaemonSettings(AvatarDaemonAppSettings):
    """Only the speech recognition, NLU and the chat: no skills, no voiceover, no images"""
    templates: list[Template] = field(default_factory=list)
    stt: str = Stt.NEMOTRON
    intent_source: str = IntentSource.CHROMA

    def create_stt_service(self, app: KaiaApp, state: State):
        if self.stt == Stt.NEMOTRON:
            return StreamingSTTService(state, app.brainbox_cache_folder)
        if self.stt == Stt.NEMOTRON_LANGUAGES:
            return StreamingSTTService(state, app.brainbox_cache_folder, languages=Stt.LANGUAGES)
        if self.stt == Stt.WHISPER_KENLM:
            return SilenceSkippingWhisperKenLMSTTService(state, app.brainbox_cache_folder, languages=Stt.LANGUAGES)
        raise ValueError(f"Unknown STT `{self.stt}`, expected one of {Stt.ALL}")

    def create_nlu_service(self, app: KaiaApp, state: State):
        ner = NerTrainingPipeline()
        return ReportingNLUService(slots_adapter=ner.ADAPTER, slots_model=ner.model_id, intent_source=self.intent_source)

    def create_testbed_service(self, app: KaiaApp, state: State):
        return TestbedService(self.templates)

    def create_chat_service(self, app: KaiaApp, state: State):
        return TestbedChatService(app.brainbox_cache_folder)

    def create_sound_event_to_stt_command(self, app: KaiaApp, state: State):
        # The first recognition after the start waits for the model to load
        return STTIntegrationService(app.brainbox_cache_folder, 16000, False, results_timeout_in_seconds=30)

    def create_silence_level_controller(self, app: KaiaApp, state: State):
        # 0.1 of Kaia is above the speech of a laptop microphone, which is about 0.01
        return SilenceLevelService(0.004)

    def create_image_service(self, app: KaiaApp, state: State):
        return None

    def create_narration_service(self, app: KaiaApp, state: State):
        return None

    def create_paraphrase_service(self, app: KaiaApp, state: State):
        return None

    def create_state_to_utterances_application(self, app: KaiaApp, state: State):
        return None

    def create_voiceover_service(self, app: KaiaApp, state: State):
        return None

    def create_text_command_to_tts_command(self, app: KaiaApp, state: State):
        return None

    def create_volume_control_service(self, app: KaiaApp, state: State):
        return None


def testbed_deciders(stt: str | None = None) -> BrainBoxSetup:
    """The deciders of the testbed: the ones the speech recognition `stt` needs, or all of them if it is None"""
    setup = BrainBoxSetup()
    if stt is None or stt in (Stt.NEMOTRON, Stt.NEMOTRON_LANGUAGES):
        setup.up(Nemotron, model='multilingual')
    # WhisperKenLM is also needed for the training of KenLM
    setup.up(WhisperKenLM).up(Chroma).up(LlamaLoraServer, parameter=NerTrainingPipeline().model_id).up(LlamaLoraSFTTrainer)
    return setup


def set_up_deciders(api: BrainBox.Api, setup: BrainBoxSetup):
    # BrainBoxSetup installs the deciders with a parameter last, but the self-test of LlamaLoraSFTTrainer needs LlamaLoraServer
    BrainBoxSetup().up(LlamaLoraServer, parameter=NerTrainingPipeline().model_id).execute(api)
    setup.execute(api)


BRAINBOX_PORT = 8090


def run_inference_brainbox(working_folder: Path | None = None):
    """
    The BrainBox of the testbed. It runs apart from the testbed, so its deciders stay up between the runs of the testbed,
    and on the port of the research BrainBox, so only one of them can run at a time.
    The resources (the models) are shared with the research BrainBox; the cache, the database and the self-tests
    are in `working_folder`/brainbox, and the testbed takes the cache from there.
    """
    if working_folder is None:
        working_folder = Loc.data_folder/'nlu-testbed'
    settings = BrainBoxServerSettings(
        registry=ControllerRegistry.discover(),
        planner=AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart),
        locations=BrainBoxLocations.default(working_folder/'brainbox'),
        stop_controllers_at_termination=False,
        port=BRAINBOX_PORT,
    )
    BrainBoxServer(settings)()


def _check_inference_brainbox(api: BrainBox.Api, cache_folder: Path):
    try:
        requests.get(f'{api.base_url}/heartbeat', timeout=1)
    except requests.ConnectionError:
        raise RuntimeError(f"No BrainBox at {api.base_url}: start run_inference_brainbox") from None
    # The avatar and the BrainBox exchange the recordings through the cache, so it must be the same folder
    probe = 'nlu-testbed-probe'
    cache_folder.mkdir(parents=True, exist_ok=True)
    (cache_folder/probe).write_text(probe)
    try:
        same_cache = api.cache.is_file(probe)
    finally:
        (cache_folder/probe).unlink()
    if not same_cache:
        raise RuntimeError(f"The BrainBox at {api.base_url} does not use the cache {cache_folder}, "
                           f"probably it is the research BrainBox: bring it down and start run_inference_brainbox")


def run_nlu_testbed(
        templates: list[Template],
        folder: Path,
        stt: str = Stt.NEMOTRON,
        intent_source: str = IntentSource.CHROMA,
        working_folder: Path | None = None,
        open_browser: bool = True,
        deploy_models: bool = True,
):
    """
    Deploys Ultimate NLU trained by train_ultimate_nlu on `folder` and starts the testbed on `templates`:
    a web page with the microphone and the chat, where every phrase gets the report of the NLU.
    The BrainBox started by run_inference_brainbox with the same `working_folder` must be running.
    Without `deploy_models`, the testbed works with the models that were deployed the last time, whatever they are.
    """
    if working_folder is None:
        working_folder = Loc.data_folder/'nlu-testbed'
    app = KaiaApp(working_folder)
    app.brainbox_api = BrainBox.Api(f'http://127.0.0.1:{BRAINBOX_PORT}')
    app.brainbox_cache_folder = working_folder/'brainbox'/'cache'
    _check_inference_brainbox(app.brainbox_api, app.brainbox_cache_folder)

    settings = KaiaAppSettings()
    settings.kaia = None
    settings.brainbox = None
    settings.avatar_server.custom_html = (Path(__file__).parent/'index.html').read_text()
    settings.avatar_processor = TestbedDaemonSettings(templates=templates, stt=stt, intent_source=intent_source)
    settings.brainbox_setup = testbed_deciders(stt)
    settings.bind_app(app)

    set_up_deciders(app.brainbox_api, settings.brainbox_setup)
    if deploy_models:
        # A separate client: the app's one is pickled into the forks, and API clients keep the last request,
        # which for uploads holds a generator that cannot be pickled.
        deploy_ultimate_nlu(BrainBox.Api(app.brainbox_api.base_url), folder)

    compile_frontend(working_folder/'avatar'/'frontend')
    app.get_fork_app(None).run()
    app.avatar_api.wait_for_connection(30)
    if open_browser:
        webbrowser.open(f'http://127.0.0.1:{settings.avatar_server.port}')
    while True:
        time.sleep(1)
