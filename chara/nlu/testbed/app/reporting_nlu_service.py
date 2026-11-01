from dataclasses import dataclass
from datetime import datetime
from typing import Any
from brainbox import BrainBox
from grammatron import Utterance
from avatar.daemon import NLUService, NLUTextEvent, RecognitionEvent, BrainBoxService
from avatar.daemon.common import IMessage, message_handler, SoundStreamingStartEvent, SoundStreamingEndEvent


def _local(timestamp: datetime | None) -> datetime | None:
    # The browser stamps its messages in UTC, the daemon and BrainBox in naive local time
    if timestamp is None or timestamp.tzinfo is None:
        return timestamp
    return timestamp.astimezone().replace(tzinfo=None)


def _time(timestamp: datetime) -> str:
    return timestamp.strftime('%H:%M:%S.%f')[:-3]


def _delta(name: str, start: datetime | None, end: datetime | None) -> str | None:
    if start is None or end is None:
        return None
    return f'{name} +{(end - start).total_seconds():.2f}s'


@dataclass
class NLULatency:
    """
    When each stage of the recognition of one text finished. The recording and the STT are the timestamps
    of the avatar messages, Chroma and NER are the finish of their BrainBox jobs.
    """
    recording_started: datetime | None = None
    recording_finished: datetime | None = None
    stt_finished: datetime | None = None
    chroma_finished: datetime | None = None
    ner_finished: datetime | None = None
    emitted: datetime | None = None

    def to_str(self) -> str:
        parts = []
        if self.recording_started is not None and self.recording_finished is not None:
            duration = (self.recording_finished - self.recording_started).total_seconds()
            parts.append(f'recorded {_time(self.recording_started)}-{_time(self.recording_finished)} ({duration:.2f}s)')
        parts.append(_delta('stt', self.recording_finished, self.stt_finished))
        parts.append(_delta('chroma', self.stt_finished, self.chroma_finished))
        parts.append(_delta('ner', self.stt_finished, self.ner_finished))
        parts.append(_delta('emitted', self.recording_finished, self.emitted))
        return 'latency: ' + ' | '.join(part for part in parts if part is not None)


@dataclass
class NLUReportEvent(IMessage):
    """Everything NLUService saw while recognizing one text"""
    file_id: str
    text: str | None
    neighbors: list[dict] | None
    slots: str | None
    recognition: str | Utterance | None
    error: Any = None
    latency: NLULatency | None = None

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
        if self.latency is not None:
            lines.append(self.latency.to_str())
        return '\n'.join(lines)


def _label(intent: str) -> str:
    return '.'.join(intent.split('.')[-2:])


def _recording(file_id: str) -> str:
    return file_id.split('.')[0]


class ReportingNLUService(NLUService):
    """
    NLUService that also reports the neighbors from Chroma, the raw output of the slots model and the latency.
    Without `brainbox_api`, the latency has no Chroma and NER.
    """
    def __init__(self, *args, brainbox_api: BrainBox.Api | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.brainbox_api = brainbox_api
        self._results: list[dict] | None = None
        self.recording_started: dict[str, datetime] = {}
        self.recording_finished: dict[str, datetime] = {}

    @message_handler
    def on_streaming_start(self, event: SoundStreamingStartEvent) -> None:
        self.recording_started[_recording(event.file_id)] = _local(event.envelop.timestamp)

    @message_handler
    def on_streaming_end(self, event: SoundStreamingEndEvent) -> None:
        recording = _recording(event.file_id)
        if not event.success:
            self.recording_started.pop(recording, None)
            return
        self.recording_finished[recording] = _local(event.envelop.timestamp)

    def parse_nlu_results(self, intent_to_template, results):
        self._results = results
        return super().parse_nlu_results(intent_to_template, results)

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def recognize(self, event: NLUTextEvent) -> tuple[RecognitionEvent | NLUReportEvent, ...]:
        self._results = None
        recognition = super().recognize(event).ensure_envelop()
        items = {item['tags']['kind']: item for item in (self._results or [])}
        results = {kind: item['result'] for kind, item in items.items()}
        report = NLUReportEvent(
            event.file_id,
            event.text,
            results.get('neighbors'),
            results.get('slots'),
            recognition.recognition,
            recognition.error,
            self._latency(event, recognition, items),
        )
        return recognition, report

    def _latency(self, event: NLUTextEvent, recognition: RecognitionEvent, items: dict[str, dict]) -> NLULatency:
        recording = _recording(event.file_id)
        finished = {}
        if self.brainbox_api is not None and len(items) > 0:
            ids = {kind: item['id'] for kind, item in items.items()}
            summaries = self.brainbox_api.jobs.get_job_summaries(list(ids.values()))
            finished = {kind: _local(summary.finished_timestamp) for kind, summary in zip(ids, summaries)}
        return NLULatency(
            recording_started=self.recording_started.pop(recording, None),
            recording_finished=self.recording_finished.pop(recording, None),
            stt_finished=_local(event.envelop.timestamp),
            chroma_finished=finished.get('neighbors'),
            ner_finished=finished.get('slots'),
            emitted=_local(recognition.envelop.timestamp),
        )
