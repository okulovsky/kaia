from dataclasses import dataclass

from ....common import Node
from ...model import Paragraph, ParagraphArray, TextCache


@dataclass
class Context:
    text: str
    paragraphs: ParagraphArray
    block: Node

@dataclass
class Selection:
    text: str
    paragraphs: ParagraphArray
    blocks: list[Node]


@dataclass
class SelectionCase:
    before: Context
    after: Context
    selection: Selection

    @staticmethod
    def parse(
            file_node: Node,
            before_selection: str,
            selection: str,
            after_selection: str) -> 'SelectionCase':

        full_text = before_selection + selection + after_selection
        if file_node[TextCache].text != full_text:
            raise ValueError('before_selection + selection + after_selection does not match the file content')

        paragraphs = file_node[TextCache].paragraphs
        spans = _paragraph_spans(paragraphs)
        blocks = _assign_blocks(file_node)

        selection_start = len(before_selection)
        selection_end = selection_start + len(selection)

        intersecting = [i for i, (start, end) in enumerate(spans) if
                        _overlaps(selection_start, selection_end, start, end)]
        if not intersecting:
            raise ValueError('selection does not intersect any paragraph')

        first_idx = intersecting[0]
        last_idx = intersecting[-1]
        before_block = blocks[first_idx]
        after_block = blocks[last_idx]

        before_paragraphs = []
        i = first_idx - 1
        while i >= 0 and blocks[i] is before_block:
            before_paragraphs.append(paragraphs[i])
            i -= 1
        before_paragraphs.reverse()
        before_paragraphs = ParagraphArray(*before_paragraphs)
        before_text = full_text[spans[first_idx][0]:selection_start]

        after_paragraphs = []
        i = last_idx + 1
        while i < len(paragraphs) and blocks[i] is after_block:
            after_paragraphs.append(paragraphs[i])
            i += 1
        after_paragraphs = ParagraphArray(*after_paragraphs)
        after_text = full_text[selection_end:spans[last_idx][1]]

        selection_paragraphs = ParagraphArray(*(paragraphs[i] for i in intersecting))
        selection_blocks = []
        for i in intersecting:
            if not selection_blocks or selection_blocks[-1] is not blocks[i]:
                selection_blocks.append(blocks[i])

        return SelectionCase(
            before=Context(before_text, before_paragraphs, before_block),
            after=Context(after_text, after_paragraphs, after_block),
            selection=Selection(selection, selection_paragraphs, selection_blocks),
        )




def _paragraph_spans(paragraphs: list[Paragraph]) -> list[tuple[int, int]]:
    spans = []
    pos = 0
    for i, paragraph in enumerate(paragraphs):
        length = len(paragraph.content)
        spans.append((pos, pos + length))
        pos += length
        if i < len(paragraphs) - 1:
            pos += 1
    return spans


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    if a_start == a_end:
        return b_start <= a_start <= b_end
    return a_start < b_end and b_start < a_end


def _assign_blocks(file_node: Node) -> list[Node]:
    assignment = []
    for section in file_node.children:
        for block in section.children:
            assignment.extend([block] * len(block[TextCache].paragraphs))
    return assignment



