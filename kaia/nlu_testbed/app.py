import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from grammatron import Template
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc
from avatar.app import compile_frontend
from avatar.daemon import StreamingSTTService, STTIntegrationService, SilenceLevelService, State
from avatar.daemon.streaming_stt_service import IntentSource
from brainbox import BrainBox
from brainbox.framework import BrainBoxSetup
from brainbox.deciders import WhisperKenLM, Nemotron, Chroma, LlamaLoraSFTTrainer, LlamaLoraServer, Ollama
from chara.common import Chara
from chara.nlu.ner_training import NerTrainingPipeline
from chara.nlu.scripts import create_dataset, create_negatives, train_ultimate_nlu
from kaia.app import KaiaAppSettings, AvatarDaemonAppSettings, KaiaApp
from .reporting_nlu_service import ReportingNLUService
from .testbed_service import TestbedService, TestbedChatService
from .silence_skipping_stt_service import SilenceSkippingWhisperKenLMSTTService


class Stt:
    NEMOTRON = 'nemotron'
    WHISPER_KENLM = 'whisper-kenlm'
    ALL = (NEMOTRON, WHISPER_KENLM)


@dataclass
class TestbedDaemonSettings(AvatarDaemonAppSettings):
    """Only the speech recognition, NLU and the chat: no skills, no voiceover, no images"""
    templates: list[Template] = field(default_factory=list)
    stt: str = Stt.NEMOTRON
    intent_source: str = IntentSource.CHROMA

    def create_stt_service(self, app: KaiaApp, state: State):
        if self.stt == Stt.NEMOTRON:
            return StreamingSTTService(state, app.brainbox_cache_folder)
        if self.stt == Stt.WHISPER_KENLM:
            return SilenceSkippingWhisperKenLMSTTService(state, app.brainbox_cache_folder)
        raise ValueError(f"Unknown STT `{self.stt}`, expected one of {Stt.ALL}")

    def create_nlu_service(self, app: KaiaApp, state: State):
        ner = NerTrainingPipeline()
        return ReportingNLUService(slots_adapter=ner.ADAPTER, slots_model=ner.model_id, intent_source=self.intent_source)

    def create_testbed_service(self, app: KaiaApp, state: State):
        return TestbedService(self.templates)

    def create_chat_service(self, app: KaiaApp, state: State):
        return TestbedChatService()

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


def run_nlu_testbed(
        templates: list[Template],
        folder: Path,
        stt: str = Stt.NEMOTRON,
        intent_source: str = IntentSource.CHROMA,
        generation_model: str | None = None,
        working_folder: Path | None = None,
        open_browser: bool = True,
):
    """
    Trains Ultimate NLU on `templates` in `folder` (see chara/nlu/scripts) and starts the testbed:
    a web page with the microphone and the chat, where every phrase gets the report of the NLU.
    With `generation_model`, a new run of paraphrases and negatives is added to `folder` first; it needs this model in Ollama.
    The training is restored from the cache while the dataset and the negatives are the same.
    """
    if working_folder is None:
        working_folder = Loc.data_folder/'nlu-testbed'
    compile_frontend(working_folder/'avatar'/'frontend')

    settings = KaiaAppSettings()
    settings.kaia = None
    settings.brainbox.deciders_files_in_kaia_working_folder = False
    settings.avatar_server.custom_html = (Path(__file__).parent/'index.html').read_text()
    settings.avatar_processor = TestbedDaemonSettings(templates=templates, stt=stt, intent_source=intent_source)
    ner = NerTrainingPipeline()
    settings.brainbox_setup = BrainBoxSetup()
    if stt == Stt.NEMOTRON:
        settings.brainbox_setup.up(Nemotron, model='multilingual')
    # WhisperKenLM is also needed for the training of KenLM
    settings.brainbox_setup.up(WhisperKenLM).up(Chroma).up(LlamaLoraServer, parameter=ner.model_id).up(LlamaLoraSFTTrainer)
    if generation_model is not None:
        settings.brainbox_setup.up(Ollama)
    app = settings.create_app(working_folder)

    with Fork(app.brainbox_server):
        app.brainbox_api.wait_for_connection(30)
        # BrainBoxSetup installs the deciders with a parameter last, but the self-test of LlamaLoraSFTTrainer needs LlamaLoraServer
        BrainBoxSetup().up(LlamaLoraServer, parameter=ner.model_id).execute(app.brainbox_api)
        settings.brainbox_setup.execute(app.brainbox_api)

        # A separate client: the app's one is pickled into the forks, and API clients keep the last request,
        # which for uploads holds a generator that cannot be pickled.
        Chara.Apis.brainbox_api = BrainBox.Api(app.brainbox_api.base_url)
        if generation_model is not None:
            create_dataset(templates, generation_model, folder=folder)
            create_negatives(generation_model, folder=folder)
        print(train_ultimate_nlu(folder))

        app.get_fork_app(None).run()
        app.avatar_api.wait_for_connection(30)
        if open_browser:
            webbrowser.open(f'http://127.0.0.1:{settings.avatar_server.port}')
        while True:
            time.sleep(1)
