import re
from dataclasses import dataclass

WORD_PATTERN = re.compile("""[a-zA-Zа-яА-ЯёЁ]+(?:['-][a-zA-Zа-яА-ЯёЁ]+)*""")

class WordProcessor:
    @dataclass
    class Fragment:
        fragment: str
        is_word: bool

    @staticmethod
    def word_split(text: str) -> list['WordProcessor.Fragment']:
        result = []
        last_pos = 0

        for match in WORD_PATTERN.finditer(text):
            start, end = match.span()
            if start > last_pos:
                result.append(WordProcessor.Fragment(text[last_pos:start], False))
            # Word fragment
            result.append(WordProcessor.Fragment(match.group(), True))
            last_pos = end

        # Remainder after the last match
        if last_pos < len(text):
            result.append(WordProcessor.Fragment(text[last_pos:], False))

        return result

    @staticmethod
    def words_only(text: str) -> list[str]:
        return [z.fragment for z in WordProcessor.word_split(text) if z.is_word]
