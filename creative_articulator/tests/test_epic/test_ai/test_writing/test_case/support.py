import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from creative_articulator.common import Node
from creative_articulator.epic.model import (
    Algorithms,
    CreativeArticulatorData,
    CreativeArticulatorLocations,
    CreativeArticulatorSettings,
    IdToNode,
    ILoader,
)

NAMESPACES = (
    'creative_articulator.epic.model.basics',
    'creative_articulator.epic.ai.background',
)
FILE_ID = 'the-file'


class _OneFileLoader(ILoader):
    def __init__(self, text: str):
        self.text = text
        self.modified = datetime.now(timezone.utc)

    def get_ids(self) -> list[str]:
        return [FILE_ID]

    def get_text(self, id: str) -> str:
        return self.text

    def get_modified(self, id: str) -> datetime:
        return self.modified


@dataclass
class Initialized:
    tmp: tempfile.TemporaryDirectory
    file_node: Node
    blocks: list[Node]
    before_selection: str
    selection: str
    after_selection: str


def initialize(text: str) -> Initialized:
    selection_start = text.index('^')
    without_start = text[:selection_start] + text[selection_start + 1:]
    selection_end = without_start.index('$')
    clean_text = without_start[:selection_end] + without_start[selection_end + 1:]

    tmp = tempfile.TemporaryDirectory()
    settings = CreativeArticulatorSettings(
        CreativeArticulatorLocations(Path(tmp.name)),
        NAMESPACES,
        _OneFileLoader(clean_text),
        Algorithms(),
    )
    data = CreativeArticulatorData(Node(), settings)
    data.synchronize()
    file_node = data.root[IdToNode][FILE_ID]

    return Initialized(
        tmp=tmp,
        file_node=file_node,
        blocks=[block for section in file_node.children for block in section.children],
        before_selection=clean_text[:selection_start],
        selection=clean_text[selection_start:selection_end],
        after_selection=clean_text[selection_end:],
    )


EXAMPLE = """
1st paragraph of the first block
2nd paragraph of the first block
***
1st paragraph of the second block
2nd paragraph of the second block
***
1st paragraph of the third block
2nd paragraph of t^he third block
3rd paragraph of t$he third block
4th paragraph of the fourth block
***
1st paragraph of the fifth block
2nd paragraph of the fifth block """
