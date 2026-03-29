import json
import re
from grammatron import GrammarRule
from abc import ABC, abstractmethod


class GrammarPrompter:
    def __call__(self, paraphrase: str) -> str:
        variables = re.findall(r'\{([^}]+)\}', paraphrase)
        example = {v: 'accusative' for v in variables}
        ## Jinja template here, bc it will also be important for German language
        return (
            f'In this Russian sentence: "{paraphrase}"\n'
            f'What grammatical case is each variable in?\n'
            f'Answer in JSON using case names: nominative, genitive, dative, accusative, instrumental, prepositional.\n'
            f'Example format: {json.dumps(example)}'
        )

    @abstractmethod
    def parse_case_response(self, s: str) -> dict[str, GrammarRule]:  # Return the entire grammar rule, also because of other languages
        pass

class RuGrammarPrompter(GrammarPrompter):
    def parse_case_response(self, s: str) -> dict[str, GrammarRule]:
        #Convert to RuGrammarRule
        return {k: RuDeclension[v.upper()] for k, v in json.loads(s).items()}

