import typing
from dataclasses import dataclass

@dataclass
class NounGrammar:
    genus: tuple[str, ...] | None = None
    plural: tuple[str, ...] | None = None
    singular: tuple[str, ...] | None = None

    def has_short(self, length: int = 1):
        for w in self.plural + self.singular:
            if len(w) <= length:
                return True
        return False

    def correct_genus(self):
        if self.genus is None or len(self.genus) == 0:
            return False
        for w in self.genus:
            if w not in {'n', 'm', 'f'}:
                return False
        return True

    def grammar_error(self) -> str|None:
        if self.genus is None or self.singular is None or self.plural is None:
            return "Incomplete grammar"
        if len(self.singular) != 1:
            return "No singular"
        if self.has_short(1):
            return "No plurar or singular form"
        if not self.correct_genus():
            return "Incorrect genus"
        return None


    @staticmethod
    def build_unified_grammar(grammars: tuple['NounGrammar',...]) -> typing.Optional['NounGrammar']:
        if len(grammars) == 0:
            return None
        uni = {}
        for g in grammars:
            for key, value in g.__dict__.items():
                if key not in uni or uni[key] is None:
                    uni[key] = value
                else:
                    if value is not None and uni[key] != value:
                        return None
        return NounGrammar(**uni)


    @staticmethod
    def parse_wiktionary_to_grammars(wiktionary: str) -> tuple['NounGrammar',...]:
        parse = {
            '|Genus': 'genus',
            '|Nominativ Plural': 'plural',
            '|Nominativ Singular': 'singular'
        }

        grammars = [{}]
        meanings = 0
        for line in wiktionary.split('\n'):
            for key, value in parse.items():
                if line.startswith(key):
                    pkey = parse[key]
                    if pkey not in grammars[-1]:
                        grammars[-1][pkey] = []
                    grammars[-1][pkey].append(line.split('=')[-1].strip())

            if line.startswith('=== {{Wortart|Substantiv|Deutsch}}'):
                meanings += 1
                if meanings >= 2 or len(grammars[-1]) > 0:
                    grammars.append({})
        result = []
        for grammar in grammars:
            g = {key: tuple(sorted(set(v))) for key, v in grammar.items()}
            result.append(NounGrammar(**g))
        return tuple(result)

    @staticmethod
    def parse_wiktionary(wiktionary):
        return NounGrammar.build_unified_grammar(NounGrammar.parse_wiktionary_to_grammars(wiktionary))