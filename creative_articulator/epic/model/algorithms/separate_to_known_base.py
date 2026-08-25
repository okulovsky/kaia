from .text_fragment import TextFragment
from .collate import collate, DEFAULT_MIN_MATCH
from .separate_to_small_blocks import _split_points, separate_by_points
from ..basics import ParagraphArray

_PRESERVED_BLOCK_BONUS = 3.0


def separate_to_known_base(text: ParagraphArray, base: list[TextFragment], max_length: int, min_match: float = DEFAULT_MIN_MATCH) -> list[TextFragment]:
    """
    This must separate the big plain text in the smaller chunks (no more than max_length).
    In this scenario, we already have an original separation, so if there is a possibility to
    separate the new paragraphs in such a way that some of the old blocks are preserved, it should be done.
    If not, separate somehow, of course.
    """
    if len(text) == 0:
        return []

    known = set()
    for fragment in base:
        known.add(tuple(paragraph.content for paragraph in fragment.paragraphs))

    contents = tuple(paragraph.content for paragraph in text)

    def bonus(start: int, stop: int) -> float:
        if contents[start:stop] in known:
            return _PRESERVED_BLOCK_BONUS
        return 0.0

    fragments = separate_by_points(text, _split_points(text, max_length, bonus))
    collate(tuple(fragments), tuple(base), min_match)
    return fragments
