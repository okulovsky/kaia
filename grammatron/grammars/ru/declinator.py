import re
from pymorphy3.analyzer import Parse
from pymorphy3 import MorphAnalyzer
from typing import *
from .categories import RuCase, RuGender, RuNumber, RuAnimacy
from ..common import WordProcessor



class Declinator:
    morph = MorphAnalyzer()

    CACHE = dict()

    @staticmethod
    def get_vocabular_form(word: str) -> Parse|None:
        if word not in Declinator.CACHE:
            Declinator.CACHE[word] = None
            for p in Declinator.morph.parse(word):
                if p.score<0.01:
                    continue
                if (
                        p.tag.POS in {'NOUN', 'ADJF', 'NUMR'} and
                        RuCase.NOMINATIVE.value in p.tag and
                        (p.tag.number is None or p.tag.number == RuNumber.SINGULAR.value)
                ):
                    Declinator.CACHE[word] = p
                    break
        return Declinator.CACHE[word]



    @staticmethod
    def choose_words_in_vocabular_form(words: Iterable[str]) -> Iterable[int]:
        """
        Return indices of words that are in nominative, masculine, singular form
        and are either nouns, adjectives, or numerals.
        """
        result_indices = []
        for i, word in enumerate(words):
            parse = Declinator.get_vocabular_form(word)
            if parse is not None:
                result_indices.append(i)
        return result_indices

    @staticmethod
    def inflect_word(
            word: str,
            case: Optional[Union[RuCase, str]] = None,
            gender: Optional[Union[RuGender, str]] = None,
            number: Optional[Union[RuNumber, str]] = None,
            animacy: Optional[Union[RuAnimacy, str]] = None,
    ) -> str:
        parse = Declinator.get_vocabular_form(word)
        if parse is None:
            return word

        (case, gender, number, animacy) = [
            v.value if v is not None and not isinstance(v, str) else v
            for v in [case, gender, number, animacy]
        ]

        target_grammemes = set()

        if parse.normal_form == 'два' and gender == RuGender.FEMININE.value:
            parse = Declinator.get_vocabular_form('две')

        if case is not None:
            target_grammemes.add(case)
        if gender is not None and (parse.tag.POS == 'ADJF' or parse.normal_form == 'один'):
            target_grammemes.add(gender)

        if number == RuNumber.MIXED.value:
            # After numerals 2–4: adjectives take plural, nouns take singular.
            if parse.tag.POS == 'ADJF':
                target_grammemes.add(RuNumber.PLURAL.value)
            elif parse.tag.POS == 'NOUN':
                target_grammemes.add(RuNumber.SINGULAR.value)
        elif number is not None and parse.tag.POS != 'NUMR':
            target_grammemes.add(number)

        # Animacy only affects accusative forms.
        # For adjectives: only masculine singular or any plural. Use the requested gender
        # (not the base-form gender) so feminine/neuter forms of 'один' are not broken.
        if animacy is not None and case == RuCase.ACCUSATIVE.value:
            if parse.tag.POS == 'NUMR':
                target_grammemes.add(animacy)
            elif parse.tag.POS == 'ADJF':
                effective_gender = gender if gender is not None else parse.tag.gender
                if number == RuNumber.PLURAL.value or effective_gender == RuGender.MASCULINE.value:
                    target_grammemes.add(animacy)

        form = parse.inflect(target_grammemes)
        if form:
            return form.word

        return word

    @staticmethod
    def declinate(text: str,
                  case: RuCase|None = None,
                  gender: RuGender|None = None,
                  number: RuNumber|None = None,
                  animacy: RuAnimacy|None = None,
                  word_selector: Optional[Callable[[Iterable[str]], Iterable[int]]] = None,
                  ):
        if word_selector is None:
            word_selector = Declinator.choose_words_in_vocabular_form
        fragments = WordProcessor.word_split(text)
        word_to_fragment = {}
        words = []
        all_fragments_texts = []
        for index, f in enumerate(fragments):
            if f.is_word:
                word_to_fragment[len(words)] = index
                words.append(f.fragment)
            all_fragments_texts.append(f.fragment)
        selected_words = word_selector(words)
        for index in selected_words:
            all_fragments_texts[word_to_fragment[index]] = Declinator.inflect_word(
                words[index], case, gender, number, animacy
            )
        return ''.join(all_fragments_texts)



