from dataclasses import dataclass

from brainbox import BrainBox
from brainbox.deciders import Chroma, Collector, WhisperKenLM, LlamaLoraServer
from brainbox.framework import JobRequest
from grammatron import LanguageDispatchDub, Template

from .recognition_setup import IPostprocessor, IRecognitionSetup, RecognitionContext, STTConfirmation
from .nlu_slots import template_variables, text_to_slots, slots_to_values, intent_label, INTENT, NO_INTENT


def _has_variables(template: Template) -> bool:
    dub = template.dub
    dubs = dub.dispatch.values() if isinstance(dub, LanguageDispatchDub) else [dub]
    if any(getattr(d, 'sequences', None) is None for d in dubs):
        return True
    return len(template_variables(template)) > 0


def _without_duplicate_jobs(request: JobRequest) -> JobRequest:
    # The transcription job enters the pack twice: as its own collector record and as
    # the dependency of the Chroma lookup. Jobs are stored by id, so the duplicate must go.
    unique = {}
    for job in request.jobs:
        unique.setdefault(job.id, job)
    return JobRequest(tuple(unique.values()))


class IntentSource:
    """Who decides the intent in NluRecognitionSetup"""
    CHROMA = 'chroma'  # the nearest phrase in the Chroma index, if it is closer than the distance threshold
    LORA = 'lora'  # the slots model (LoRA): its `intent` line; Chroma is not used
    AGREEMENT = 'agreement'  # the command is accepted only if Chroma and the slots model name the same intent
    ALL = (CHROMA, LORA, AGREEMENT)


class NluPostprocessor(IPostprocessor):
    def __init__(self,
                 intent_to_template: dict[str, Template],
                 distance_threshold: float,
                 with_slots: bool = False,
                 intent_source: str = IntentSource.CHROMA,
                 ):
        if intent_source not in IntentSource.ALL:
            raise ValueError(f"Unknown intent source `{intent_source}`, expected one of {IntentSource.ALL}")
        self.intent_to_template = intent_to_template
        self.distance_threshold = distance_threshold
        self.with_slots = with_slots
        self.intent_source = intent_source
        self.label_to_intent = {intent_label(name): name for name in intent_to_template}
        self.slot_free_intents = {
            name for name, template in intent_to_template.items() if not _has_variables(template)
        }

    def postprocess(self, result):
        try:
            results = {item['tags']['kind']: item['result'] for item in result}
            text = str(results.get('text') or '')
            neighbors = results.get('neighbors') or []
            meta = dict(text=text, neighbors=neighbors)
            utterance = self._recognize(neighbors, results)
        except Exception as error:
            return STTConfirmation(None, result, error)
        # Unrecognized speech is returned as plain text: the assistant answers it with
        # AutomatonNotFoundSkill, and skills waiting for a free-text reply still receive it.
        return STTConfirmation(utterance if utterance is not None else text, meta)

    def _recognize(self, neighbors: list[dict], results: dict):
        slots = text_to_slots(str(results.get('slots') or '')) if self.with_slots else None
        model_intent = slots.pop(INTENT, None) if slots is not None else None
        intent = self._choose_intent(neighbors, model_intent)
        if intent is None:
            return None
        template = self.intent_to_template.get(intent)
        if template is None:
            return None
        if intent in self.slot_free_intents:
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

    def _choose_intent(self, neighbors: list[dict], model_intent: str | None) -> str | None:
        if self.intent_source == IntentSource.LORA:
            if model_intent is None or model_intent == NO_INTENT:
                return None
            return self.label_to_intent.get(model_intent)
        if not neighbors:
            return None
        intent = neighbors[0]['intent']
        if self.intent_source == IntentSource.AGREEMENT:
            # On misrecognized speech the two rarely agree, which rejects better than the distance threshold
            return intent if model_intent == intent_label(intent) else None
        return intent if neighbors[0]['distance'] <= self.distance_threshold else None


@dataclass
class NluRecognitionSetup(IRecognitionSetup):
    model: str = 'CORE'
    distance_threshold: float = 0.18
    kenlm_weight: float = 0.5
    beams: int = 5
    neighbors: int = 3
    collection_name: str | None = None
    languages: tuple[str, ...] | None = ('en', 'de', 'ru')
    # The LoRA adapter of LlamaLoraServer that extracts the variables, see chara/nlu/ner_training.
    # None means that the intents with variables are not recognized.
    slots_adapter: str | None = None
    slots_model: str = 'gemma-3-270m-it'
    # Who decides the intent, see IntentSource; `lora` and `agreement` need the slots adapter trained with intents
    intent_source: str = IntentSource.CHROMA

    def __post_init__(self):
        if self.intent_source not in IntentSource.ALL:
            raise ValueError(f"Unknown intent source `{self.intent_source}`, expected one of {IntentSource.ALL}")
        if self.intent_source != IntentSource.CHROMA and self.slots_adapter is None:
            raise ValueError(f"The intent source `{self.intent_source}` needs `slots_adapter`")

    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        base_id = context.command.file.split('.')[0]
        transcription = (
            WhisperKenLM
            .new_task(id=base_id + '.nlu-stt')
            .transcribe(
                file=context.command.file,
                weight=self.kenlm_weight,
                beams=self.beams,
                languages=list(self.languages) if self.languages else None,
            )
        )
        builder = Collector.TaskBuilder()
        builder.append(transcription, dict(kind='text'))
        if self.intent_source != IntentSource.LORA:
            lookup = (
                Chroma
                .new_task(id=base_id + '.nlu-intent')
                .find_neighbors(text=transcription, k=self.neighbors, collection_name=self.collection_name)
            )
            builder.append(lookup, dict(kind='neighbors'))
        if self.slots_adapter is not None:
            slots = (
                LlamaLoraServer
                .new_task(id=base_id + '.nlu-slots', parameter=self.slots_model)
                .completion(task_name=self.slots_adapter, prompt=transcription, max_tokens=32)
            )
            builder.append(slots, dict(kind='slots'))
        task = _without_duplicate_jobs(builder.to_collector_pack('to_array'))

        handler = context.rhasspy_handlers[self.model]
        return task, NluPostprocessor(
            handler.intent_to_template, self.distance_threshold, self.slots_adapter is not None, self.intent_source
        )
