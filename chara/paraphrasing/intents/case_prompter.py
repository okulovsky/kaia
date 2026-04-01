import json
import re
from grammatron import GrammarRule
from grammatron.grammars.ru import RuDeclension, RuGrammarRule
from abc import ABC, abstractmethod


class GrammarPrompter:
    def __call__(self, paraphrase: str) -> str:
        variables = re.findall(r'\{([^}]+)\}', paraphrase)
        example = {v: 'accusative' for v in variables}
        ## Jinja template here, bc it will also be important for German language
        return (
            f'In this Russian sentence: "{paraphrase}"\n'
            f'What grammatical case is each {{variable}} placeholder in?\n'
            f'Return ONLY a raw JSON object, no markdown, no explanation.\n'
            f'Keys are the variable names (without braces). Values are case names: nominative, genitive, dative, accusative, instrumental, prepositional.\n'
            f'Example: {json.dumps(example)}'
        )

    @abstractmethod
    def parse_case_response(self, s: str) -> dict[str, GrammarRule]:  # Return the entire grammar rule, also because of other languages
        pass

class RuGrammarPrompter(GrammarPrompter):
    def parse_case_response(self, s: str) -> dict[str, GrammarRule]:
        # Extract JSON from potential markdown code blocks
        match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', s, re.DOTALL)
        if match:
            s = match.group(1)
        else:
            match = re.search(r'\{.*\}', s, re.DOTALL)
            if match:
                s = match.group(0)
        result = {}
        for k, v in json.loads(s).items():
            try:
                result[k] = RuGrammarRule(RuDeclension[v.strip().upper()])
            except (KeyError, ValueError):
                pass
        return result

