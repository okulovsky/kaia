from .text_fragment import TextFragment
from ..basics import Paragraph, ParagraphArray, ParagraphType

_CUT_AFTER_BREAK = 0.0
_CUT_BEFORE_BLANK = 0.5
_CUT_BETWEEN_DIFFERENT = 0.5
_CUT_INSIDE_PLAIN = 1.0
_CUT_INSIDE_DIALOG = 2.0

_BREAK_TYPES = (ParagraphType.Blank, ParagraphType.Separator)


def cut_cost(previous: Paragraph, following: Paragraph) -> float:
    if previous.text_type in _BREAK_TYPES:
        return _CUT_AFTER_BREAK
    if following.text_type in _BREAK_TYPES:
        return _CUT_BEFORE_BLANK
    if previous.text_type != following.text_type:
        return _CUT_BETWEEN_DIFFERENT
    if following.text_type == ParagraphType.Dialog:
        return _CUT_INSIDE_DIALOG
    return _CUT_INSIDE_PLAIN


def fill_cost(length: int, max_length: int) -> float:
    if length >= max_length:
        return 0.0
    return ((max_length - length) / max_length) ** 2


def _split_points(text: ParagraphArray, max_length: int, bonus) -> list[int]:
    count = len(text)
    lengths = [len(paragraph.text) for paragraph in text]
    best_cost: list[float|None] = [None] * (count + 1)
    best_next: list[int|None] = [None] * (count + 1)
    best_cost[count] = 0.0

    for start in range(count - 1, -1, -1):
        length = 0
        for stop in range(start + 1, count + 1):
            length += lengths[stop - 1]
            if length > max_length and stop > start + 1:
                break
            cost = fill_cost(length, max_length) + best_cost[stop]
            if stop < count:
                cost += cut_cost(text[stop - 1], text[stop])
            if bonus is not None:
                cost -= bonus(start, stop)
            if best_cost[start] is None or cost < best_cost[start]:
                best_cost[start] = cost
                best_next[start] = stop

    points = []
    position = 0
    while position < count:
        position = best_next[position]
        points.append(position)
    return points


def separate_by_points(text: ParagraphArray, points: list[int]) -> list[TextFragment]:
    fragments = []
    start = 0
    for stop in points:
        fragments.append(TextFragment(text.subarray(start, stop), None))
        start = stop
    return fragments


def separate(text: ParagraphArray, max_length: int) -> list[TextFragment]:
    """
    This should separate text in the chunks (no longer than max_length).
    The text is a mixture of dialogs and plain text.
    The separation should tend to group the dialogs together and paragraphs of the plain text also tend to go together.
    Blocks should also tend to be bigger (within limitation of max_length)
    Some kind of dynamic programming would be nice.
    """
    if len(text) == 0:
        return []
    return separate_by_points(text, _split_points(text, max_length, None))
