from dataclasses import dataclass
from typing import Any
from grammatron import Utterance
from avatar.daemon import NLUService, NLUTextEvent, RecognitionEvent, BrainBoxService
from avatar.daemon.common import IMessage, message_handler


@dataclass
class NLUReportEvent(IMessage):
    """Everything NLUService saw while recognizing one text"""
    file_id: str
    text: str | None
    neighbors: list[dict] | None
    slots: str | None
    recognition: str | Utterance | None
    error: Any = None

    def to_str(self, neighbors_count: int = 3) -> str:
        lines = [f'text: {self.text}']
        if self.error is not None:
            lines.append(f'error: {self.error}')
        if self.neighbors is not None:
            lines.append('neighbors:')
            for neighbor in self.neighbors[:neighbors_count]:
                lines.append(f"  {neighbor['distance']:.3f} {_label(neighbor['intent'])}: {neighbor['text']}")
        if self.slots is not None:
            lines.append('slots: ' + ' | '.join(line for line in self.slots.strip().splitlines()))
        if isinstance(self.recognition, Utterance):
            lines.append(f'recognized: {_label(self.recognition.template.get_name())} {self.recognition.value}')
        else:
            lines.append('recognized: nothing')
        return '\n'.join(lines)


def _label(intent: str) -> str:
    return '.'.join(intent.split('.')[-2:])


class ReportingNLUService(NLUService):
    """NLUService that also reports the neighbors from Chroma and the raw output of the slots model"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._results: list[dict] | None = None

    def parse_nlu_results(self, intent_to_template, results):
        self._results = results
        return super().parse_nlu_results(intent_to_template, results)

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def recognize(self, event: NLUTextEvent) -> tuple[RecognitionEvent | NLUReportEvent, ...]:
        self._results = None
        recognition = super().recognize(event)
        results = {item['tags']['kind']: item['result'] for item in (self._results or [])}
        report = NLUReportEvent(
            event.file_id,
            event.text,
            results.get('neighbors'),
            results.get('slots'),
            recognition.recognition,
            recognition.error,
        )
        return recognition, report
