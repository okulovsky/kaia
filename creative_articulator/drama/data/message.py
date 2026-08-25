import uuid
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class MessageSegment:
    content: str
    is_action: bool = False

@dataclass
class MessageContent:
    segments: list[MessageSegment]

    def __str__(self) -> str:
        result = []
        for segment in self.segments:
            if segment.is_action:
                result.append(' *')
            result.append(segment.content)
            if segment.is_action:
                result.append('* ')
        return ''.join(result).replace('  ',' ')

    @staticmethod
    def parse(s: str) -> 'MessageContent':
        parts = s.split('*')
        segments = [
            MessageSegment(part, is_action=(i % 2 == 1))
            for i, part in enumerate(parts)
            if part
        ]
        return MessageContent(segments)


def _id():
    return str(uuid.uuid4())

@dataclass
class Message:
    content: MessageContent
    speaker: str|None
    from_user: bool = False
    id: str = field(default_factory=_id)

    Segment: ClassVar = MessageSegment
    Content: ClassVar = MessageContent

    def __str__(self) -> str:
        if self.speaker is None:
            return '*'+self.content.__str__()+'*'
        else:
            return self.speaker+": "+self.content.__str__()

    @staticmethod
    def parse(s: str) -> 'Message':
        if s.startswith('*'):
            return Message(MessageContent.parse(s[1:-1]), None, False)
        else:
            name, content = s.split(':', 1)
            return Message(MessageContent.parse(content.strip()), name.strip(), False)

    @staticmethod
    def from_dict(d: dict) -> 'Message':
        segments = [MessageSegment(s['content'], s['is_action']) for s in d['segments']]
        return Message(MessageContent(segments), d['speaker'], False)

    @staticmethod
    def from_text(text, speaker: str|None = None, from_user: bool = False) -> 'Message':
        return Message(MessageContent.parse(text), speaker, from_user)
