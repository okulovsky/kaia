import json
from datetime import timedelta
from enum import Enum
from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector
from foundation_kaia.misc import Loc
from grammatron import Template, VariableDub, TimedeltaDub, OrdinalDub, OptionsDub, Utterance
from avatar.daemon import (
    BrainBoxService, StreamingSTTService, WhisperKenLMSTTService, NLUService, NLUTextEvent, IntentsPack, State,
    SoundStreamingStartEvent, SoundEvent, RecognitionEvent, TemplatesRecognitionRequest, FreeSpeechRecognitionRequest,
    MAIN_CONTEXT,
)
from avatar.daemon.streaming_stt_service import IntentSource
from avatar.messaging import AvatarDaemon, AvatarClient


class Day(Enum):
    Today = 0
    Tomorrow = 1


SET_TIMER = Template(f"Set the timer for {VariableDub('duration', TimedeltaDub())}")
CANCEL_TIMER = Template('Cancel the timer', f"Cancel the {VariableDub('index', OrdinalDub(1, 10))} timer")
DATE = Template('What is the date?', f"What date is {VariableDub('delta', OptionsDub(Day))}?")
CHARACTER = Template(f"I want to talk with {VariableDub('character', OptionsDub(['Ocean', 'Forest']))}")
TIME = Template('What time is it?')
YES = Template('Yes')

# Files of the tests are named after their text
TEXTS = {'time.wav': 'What time is it', 'yes.wav': 'Yes', 'free.wav': 'Hello there'}
# The text and the language tags of each stream, as Nemotron gives them in noise
STREAMS = {
    'time.wav': {'auto': ('What time is it', ['en-US']), 'en': ('What time is it', ['en-US']), 'ru': ('Уот тайм', ['ru-RU'])},
    'light.wav': {'auto': ('liệu chi dáng', ['vi-VN']), 'en': ('', []), 'ru': ('Включи свет', ['ru-RU'])},
    'night.wav': {'auto': ('và cô mino', ['vi-VN']), 'en': ('', []), 'ru': ('', [])},
    'yes.wav': {'auto': ('yes', []), 'en': ('', []), 'ru': ('', [])},
    'da.wav': {'auto': ('', []), 'en': ('yeah', ['en-US']), 'ru': ('Да', ['ru-RU'])},
}


class NemotronMock(ISelfManagingDecider):
    def __init__(self, folder):
        self.folder = folder
        self.languages = []

    def get_name(self):
        return 'Nemotron'

    def transcribe_stream(self, audio, language: str = 'auto', sample_rate: int = 16000, model: str | None = None):
        self.languages.append(language)
        if audio not in TEXTS:
            raise ValueError("Upstream job aborted")
        text = TEXTS[audio]
        lines = [dict(text=text[:3], is_final=False), dict(text=text, is_final=True)]
        name = audio + '.jsonl'
        (self.folder / name).write_text(''.join(json.dumps(line) + '\n' for line in lines))
        return name

    def transcribe_stream_languages(self, audio, languages: list[str], sample_rate: int = 16000, model: str | None = None):
        self.languages.append(languages)
        lines = []
        for stream in languages:
            text, tags = STREAMS[audio][stream]
            lines += [dict(text=text[:3], is_final=False, stream=stream), dict(text=text, is_final=True, languages=tags, stream=stream)]
        name = audio + '.jsonl'
        (self.folder / name).write_text(''.join(json.dumps(line) + '\n' for line in lines))
        return name


class WhisperKenLMMock(ISelfManagingDecider):
    def __init__(self):
        self.languages = []

    def get_name(self):
        return 'WhisperKenLM'

    def transcribe(self, file, weight: float = 0.5, beams: int = 5, languages: list[str] | None = None) -> str:
        self.languages.append(languages)
        return TEXTS[file]


class ChromaMock(ISelfManagingDecider):
    def get_name(self):
        return 'Chroma'

    def find_neighbors(self, text: str, k: int = 5, collection_name: str | None = None) -> list[dict]:
        # The closest neighbour is always from another context
        return [dict(text='Yes', intent=YES.get_name(), distance=0.01), dict(text=text, intent=TIME.get_name(), distance=0.05)]


class LlamaLoraServerMock(ISelfManagingDecider):
    def get_name(self):
        return 'LlamaLoraServer'

    def completion(self, task_name: str, prompt: str, max_tokens: int = 32):
        return f'\nintent: {YES.get_name()}'


def _result(text, intent, slots=None, distance=0.05):
    result = [dict(tags=dict(kind='neighbors'), result=[dict(text=text, intent=intent, distance=distance)])]
    if slots is not None:
        result.append(dict(tags=dict(kind='slots'), result=slots))
    return result


class TranscriptionTestCase(TestCase):
    def setUp(self):
        self.temp_folder = Loc.create_test_folder()
        self.folder = self.temp_folder.__enter__()
        self.nemotron = NemotronMock(self.folder)
        self.whisper = WhisperKenLMMock()

    def tearDown(self):
        self.temp_folder.__exit__(None, None, None)

    def run_service(self, service, *messages):
        self.service = service
        with BrainBox.Api.serverless_test([self.nemotron, self.whisper]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            proc.rules.bind(service)
            proc.rules.bind(BrainBoxService(api))
            return proc.debug_and_stop_by_message_type(NLUTextEvent, *messages).messages[-1]

    def test_nemotron_free_speech(self):
        request = FreeSpeechRecognitionRequest()
        result = self.run_service(StreamingSTTService(State(language='de'), self.folder), request, SoundStreamingStartEvent('free.wav'))
        self.assertEqual('free.wav', result.file_id)
        self.assertEqual('Hello there', result.text)
        self.assertEqual(request, result.request)
        self.assertIsNone(result.error)
        self.assertEqual(['de'], self.nemotron.languages)

    def test_nemotron_templates(self):
        result = self.run_service(StreamingSTTService(State(language='de'), self.folder), SoundStreamingStartEvent('time.wav'))
        self.assertEqual('What time is it', result.text)
        self.assertEqual(TemplatesRecognitionRequest(), result.request)
        self.assertEqual(['auto'], self.nemotron.languages)

    def test_nemotron_error_restores_the_request(self):
        request = FreeSpeechRecognitionRequest()
        result = self.run_service(StreamingSTTService(State(), self.folder), request, SoundStreamingStartEvent('cancelled.wav'))
        self.assertIsNone(result.text)
        self.assertIsNotNone(result.error)
        self.assertEqual(request, self.service.requested)

    def run_languages(self, file, state=None, *messages):
        service = StreamingSTTService(state or State(), self.folder, languages=('en', 'ru'))
        return self.run_service(service, *messages, SoundStreamingStartEvent(file))

    def test_nemotron_languages_auto_is_allowed(self):
        self.assertEqual('What time is it', self.run_languages('time.wav').text)
        self.assertEqual([['auto', 'en', 'ru']], self.nemotron.languages)

    def test_nemotron_languages_only_forced_with_text(self):
        self.assertEqual('Включи свет', self.run_languages('light.wav').text)

    def test_nemotron_languages_nothing_in_allowed_languages(self):
        self.assertEqual('', self.run_languages('night.wav').text)

    def test_nemotron_languages_auto_without_tag(self):
        self.assertEqual('yes', self.run_languages('yes.wav').text)

    def test_nemotron_languages_several_forced(self):
        self.assertEqual('yeah', self.run_languages('da.wav').text)
        self.assertEqual('Да', self.run_languages('da.wav', State(language='ru')).text)

    def test_nemotron_languages_free_speech_is_one_stream(self):
        result = self.run_languages('free.wav', State(language='de'), FreeSpeechRecognitionRequest())
        self.assertEqual('Hello there', result.text)
        self.assertEqual(['de'], self.nemotron.languages)

    def test_read_final_text(self):
        lines = [dict(text='Hel', is_final=False), dict(text='Hello', is_final=True), dict(text=' there ', is_final=True)]
        content = ''.join(json.dumps(line) + '\n' for line in lines).encode()
        self.assertEqual('Hello there', StreamingSTTService.read_final_text(content))
        self.assertEqual('Hel', StreamingSTTService.read_final_text(content.split(b'\n')[0]))

    def test_whisper_kenlm_templates(self):
        result = self.run_service(WhisperKenLMSTTService(State(language='de')), SoundEvent('time.wav'))
        self.assertEqual('time.wav', result.file_id)
        self.assertEqual('What time is it', result.text)
        self.assertEqual(TemplatesRecognitionRequest(), result.request)
        self.assertEqual([['en', 'de', 'ru']], self.whisper.languages)

    def test_whisper_kenlm_free_speech(self):
        request = FreeSpeechRecognitionRequest()
        result = self.run_service(WhisperKenLMSTTService(State(language='de')), request, SoundEvent('free.wav'))
        self.assertEqual('Hello there', result.text)
        self.assertEqual(request, result.request)
        self.assertEqual([['de']], self.whisper.languages)


class NLUServiceTestCase(TestCase):
    def run_service(self, *messages, **kwargs):
        with BrainBox.Api.serverless_test([ChromaMock(), LlamaLoraServerMock(), Collector()]) as api:
            proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
            proc.rules.bind(NLUService(**kwargs))
            proc.rules.bind(BrainBoxService(api))
            proc.client.push(NLUService.TrainingCommand([
                IntentsPack(MAIN_CONTEXT, (TIME,)),
                IntentsPack('Confirmation', (YES,)),
            ]))
            return proc.debug_and_stop_by_message_type(RecognitionEvent, *messages).messages[-1]

    def test_free_speech(self):
        result = self.run_service(NLUTextEvent('free.wav', 'Hello there', FreeSpeechRecognitionRequest()))
        self.assertEqual('free.wav', result.file_id)
        self.assertEqual('Hello there', result.recognition)
        self.assertIsNone(result.error)

    def test_templates(self):
        result = self.run_service(NLUTextEvent('time.wav', 'What time is it', TemplatesRecognitionRequest()))
        self.assertIsInstance(result.recognition, Utterance)
        self.assertEqual(TIME.get_name(), result.recognition.template.get_name())

    def test_templates_of_another_context(self):
        result = self.run_service(NLUTextEvent('yes.wav', 'Yes', TemplatesRecognitionRequest('Confirmation')))
        self.assertEqual(YES.get_name(), result.recognition.template.get_name())

    def test_lora_intent_outside_the_context(self):
        result = self.run_service(NLUTextEvent('time.wav', 'What time is it', TemplatesRecognitionRequest()),
                                  slots_adapter='nlu-slots', intent_source=IntentSource.LORA)
        self.assertEqual('What time is it', result.recognition)

    def test_unknown_context(self):
        result = self.run_service(NLUTextEvent('time.wav', 'What time is it', TemplatesRecognitionRequest('Unknown')))
        self.assertIsNone(result.recognition)
        self.assertIsNotNone(result.error)

    def test_transcription_error_is_passed(self):
        result = self.run_service(NLUTextEvent('time.wav', None, TemplatesRecognitionRequest(), 'error'))
        self.assertIsNone(result.recognition)
        self.assertEqual('error', result.error)


class PipelineTestCase(TestCase):
    def test_nemotron_to_nlu(self):
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([NemotronMock(folder), ChromaMock(), Collector()]) as api:
                proc = AvatarDaemon(AvatarClient.default(), timeout_in_pull_in_seconds=0)
                proc.rules.bind(StreamingSTTService(State(), folder))
                proc.rules.bind(NLUService())
                proc.rules.bind(BrainBoxService(api))
                proc.client.push(NLUService.TrainingCommand([IntentsPack(MAIN_CONTEXT, (TIME,))]))
                result = proc.debug_and_stop_by_message_type(RecognitionEvent, SoundStreamingStartEvent('time.wav')).messages[-1]
                self.assertEqual('time.wav', result.file_id)
                self.assertEqual(TIME.get_name(), result.recognition.template.get_name())


class NluResultsTestCase(TestCase):
    def setUp(self):
        self.templates = {t.get_name(): t for t in (SET_TIMER, CANCEL_TIMER, DATE, CHARACTER, TIME)}
        self.with_slots = NLUService(slots_adapter='nlu-slots')
        self.without_slots = NLUService()
        self.agreement = NLUService(slots_adapter='nlu-slots', intent_source=IntentSource.AGREEMENT)
        self.lora = NLUService(slots_adapter='nlu-slots', intent_source=IntentSource.LORA)

    def recognize(self, service, text, intent, slots=None, distance=0.05):
        return service.parse_nlu_results(self.templates, _result(text, intent.get_name(), slots, distance))

    def label(self, template):
        return '.'.join(template.get_name().split('.')[-2:])

    def test_slot_free_intent(self):
        self.assertIsInstance(self.recognize(self.with_slots, 'What time is it', TIME, '\n-'), Utterance)

    def test_values_are_extracted(self):
        recognition = self.recognize(self.with_slots, 'Поставь таймер на пять минут', SET_TIMER, '\nduration: 5m')
        self.assertEqual(timedelta(minutes=5), recognition.value['duration'])

    def test_no_value_said(self):
        recognition = self.recognize(self.with_slots, 'Cancel the timer', CANCEL_TIMER, '\n-')
        self.assertEqual({}, recognition.value)

    def test_missing_required_value_is_rejected(self):
        self.assertIsNone(self.recognize(self.with_slots, 'Set a timer', SET_TIMER, '\n-'))

    def test_unknown_option_is_rejected(self):
        self.assertIsNone(self.recognize(self.with_slots, 'Talk to Cliff', CHARACTER, '\ncharacter: Cliff'))

    def test_garbage_from_model_is_rejected(self):
        self.assertIsNone(self.recognize(self.with_slots, 'Set a timer', SET_TIMER, 'five minutes'))

    def test_chroma_ignores_the_intent_of_the_model(self):
        recognition = self.recognize(self.with_slots, 'Cancel the second timer', CANCEL_TIMER, f'\nintent: {self.label(TIME)}\nindex: 2')
        self.assertEqual({'index': 2}, recognition.value)
        self.assertIsNone(self.recognize(self.with_slots, 'Cancel', CANCEL_TIMER, f'\nintent: {self.label(CANCEL_TIMER)}', distance=0.5))

    def test_agreement_accepts_beyond_the_threshold(self):
        recognition = self.recognize(self.agreement, 'Cancel the second timer', CANCEL_TIMER,
                                     f'\nintent: {self.label(CANCEL_TIMER)}\nindex: 2', distance=0.5)
        self.assertEqual({'index': 2}, recognition.value)

    def test_disagreement_rejects_below_the_threshold(self):
        self.assertIsNone(self.recognize(self.agreement, 'What time is it', TIME, f'\nintent: {self.label(SET_TIMER)}', distance=0.01))

    def test_lora_decides_without_chroma(self):
        result = [dict(tags=dict(kind='slots'), result=f'\nintent: {self.label(CANCEL_TIMER)}\nindex: 2')]
        recognition = self.lora.parse_nlu_results(self.templates, result)
        self.assertEqual({'index': 2}, recognition.value)
        self.assertEqual(CANCEL_TIMER.get_name(), recognition.template.get_name())

    def test_lora_not_a_command(self):
        self.assertIsNone(self.recognize(self.lora, 'Pass the salt', TIME, '\nintent: none'))
        self.assertIsNone(self.recognize(self.lora, 'Pass the salt', TIME, '\nintent: unknown_intent'))

    def test_lora_needs_the_adapter(self):
        with self.assertRaises(ValueError):
            NLUService(intent_source=IntentSource.LORA)

    def test_without_slots_model_variables_are_rejected(self):
        self.assertIsNone(self.recognize(self.without_slots, 'Cancel the timer', CANCEL_TIMER))
