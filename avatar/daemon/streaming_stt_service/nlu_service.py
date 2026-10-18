import traceback
from brainbox.deciders import Chroma, Collector, LlamaLoraServer
from grammatron import Template, LanguageDispatchDub, Utterance
from ..common import message_handler, AvatarService
from ..brainbox_service import BrainBoxService
from ..stt_service import STTTrainingCommand, TemplatesRecognitionRequest, FreeSpeechRecognitionRequest, RecognitionEvent
from ..stt_service.stt.free_speech_recognition import FreeSpeechPostprocessor
from .nlu_slots import template_variables, text_to_slots, slots_to_values, intent_label, INTENT, NO_INTENT
from .nlu_text_event import NLUTextEvent


class IntentSource:
    """Who decides the intent in NLUService"""
    CHROMA = 'chroma'  # the nearest phrase in the Chroma index, if it is closer than the distance threshold
    LORA = 'lora'  # the slots model (LoRA): its `intent` line; Chroma is not used
    AGREEMENT = 'agreement'  # the command is accepted only if Chroma and the slots model name the same intent
    ALL = (CHROMA, LORA, AGREEMENT)


def _has_variables(template: Template) -> bool:
    dub = template.dub
    dubs = dub.dispatch.values() if isinstance(dub, LanguageDispatchDub) else [dub]
    if any(getattr(d, 'sequences', None) is None for d in dubs):
        return True
    return len(template_variables(template)) > 0


class NLUService(AvatarService):
    TrainingCommand = STTTrainingCommand

    def __init__(self,
                 distance_threshold: float = 0.18,
                 # Chroma searches the whole index, and the neighbours outside the requested context are skipped,
                 # so it is asked for more neighbours than the one that is taken
                 neighbors: int = 20,
                 collection_name: str | None = None,
                 # The LoRA adapter of LlamaLoraServer that extracts the variables, see chara/nlu/ner_training.
                 # None means that the intents with variables are not recognized.
                 slots_adapter: str | None = None,
                 slots_model: str = 'gemma-3-270m-it',
                 # Who decides the intent, see IntentSource; `lora` and `agreement` need the slots adapter trained with intents
                 intent_source: str = IntentSource.CHROMA,
                 ):
        if intent_source not in IntentSource.ALL:
            raise ValueError(f"Unknown intent source `{intent_source}`, expected one of {IntentSource.ALL}")
        if intent_source != IntentSource.CHROMA and slots_adapter is None:
            raise ValueError(f"The intent source `{intent_source}` needs `slots_adapter`")
        self.distance_threshold = distance_threshold
        self.neighbors = neighbors
        self.collection_name = collection_name
        self.slots_adapter = slots_adapter
        self.slots_model = slots_model
        self.intent_source = intent_source
        self.contexts: dict[str, dict[str, Template]] = {}

    def requires_brainbox(self):
        return True

    @message_handler
    def train(self, message: STTTrainingCommand) -> None:
        for pack in message.packs:
            self.contexts[pack.context] = {template.get_name(): template for template in pack.templates}

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def recognize(self, event: NLUTextEvent) -> RecognitionEvent:
        if event.error is not None:
            return RecognitionEvent(event.file_id, None, event.error)
        try:
            if isinstance(event.request, FreeSpeechRecognitionRequest):
                result = FreeSpeechPostprocessor(event.request.template).postprocess(event.text)
                return RecognitionEvent(event.file_id, result.recognition, result.error)
            if isinstance(event.request, TemplatesRecognitionRequest):
                return RecognitionEvent(event.file_id, self.recognize_templates(event))
            raise TypeError(f"Unknown recognition request {event.request}")
        except Exception:
            return RecognitionEvent(event.file_id, None, traceback.format_exc())

    def recognize_templates(self, event: NLUTextEvent) -> str|Utterance:
        intent_to_template = self.contexts[event.request.context]
        text = event.text
        if text.strip() == '':
            return text
        base_id = event.file_id.split('.')[0]
        builder = Collector.TaskBuilder()
        if self.intent_source != IntentSource.LORA:
            lookup = (
                Chroma
                .new_task(id=base_id + '.nlu-intent')
                .find_neighbors(text=text, k=self.neighbors, collection_name=self.collection_name)
            )
            builder.append(lookup, dict(kind='neighbors'))
        if self.slots_adapter is not None:
            slots = (
                LlamaLoraServer
                .new_task(id=base_id + '.nlu-slots', parameter=self.slots_model)
                .completion(task_name=self.slots_adapter, prompt=text, max_tokens=32)
            )
            builder.append(slots, dict(kind='slots'))
        command = BrainBoxService.Command(builder.to_collector_pack('to_array')).as_reply_to(event)
        result = self.client.run_synchronously(command, BrainBoxService.Confirmation)
        if result.result is None:
            raise ValueError(f"Expected result, error\n{result.error}")
        utterance = self.parse_nlu_results(intent_to_template, result.result)
        # Unrecognized speech is returned as plain text: the assistant answers it with
        # AutomatonNotFoundSkill, and skills waiting for a free-text reply still receive it.
        return utterance if utterance is not None else text

    def parse_nlu_results(self, intent_to_template: dict[str, Template], results: list[dict]) -> Utterance|None:
        results = {item['tags']['kind']: item['result'] for item in results}
        neighbors = [n for n in (results.get('neighbors') or []) if n['intent'] in intent_to_template]
        slots = text_to_slots(str(results.get('slots') or '')) if self.slots_adapter is not None else None
        model_intent = slots.pop(INTENT, None) if slots is not None else None
        intent = self._choose_intent(intent_to_template, neighbors, model_intent)
        if intent is None:
            return None
        template = intent_to_template[intent]
        if not _has_variables(template):
            return template.utter({})
        # Without the slots model, templates with variables are rejected: uttering them without values
        # would silently drop what the user said, e.g. "the date tomorrow" would be answered with today's date.
        if slots is None:
            return None
        values = slots_to_values(template, slots)
        if values is None:
            return None
        try:
            return template.utter(values)
        except Exception:
            # e.g. the model has seen no value, but the template has no sequence without variables
            return None

    def _choose_intent(self, intent_to_template: dict[str, Template], neighbors: list[dict], model_intent: str | None) -> str | None:
        if self.intent_source == IntentSource.LORA:
            if model_intent is None or model_intent == NO_INTENT:
                return None
            return {intent_label(name): name for name in intent_to_template}.get(model_intent)
        if not neighbors:
            return None
        intent = neighbors[0]['intent']
        if self.intent_source == IntentSource.AGREEMENT:
            # On misrecognized speech the two rarely agree, which rejects better than the distance threshold
            return intent if model_intent == intent_label(intent) else None
        return intent if neighbors[0]['distance'] <= self.distance_threshold else None
