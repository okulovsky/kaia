from dataclasses import dataclass, field


@dataclass
class TagAnnotation:
    tags: dict[str, bool]
    rejected: bool = False


@dataclass
class GlobalTags:
    accepted: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
