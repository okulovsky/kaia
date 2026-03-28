import json
import re
from grammatron.grammars.ru import RuDeclension


class CasePrompter:
    def __call__(self, paraphrase: str) -> str:
        variables = re.findall(r'\{([^}]+)\}', paraphrase)
        example = {v: 'accusative' for v in variables}
        return (
            f'In this Russian sentence: "{paraphrase}"\n'
            f'What grammatical case is each variable in?\n'
            f'Answer in JSON using case names: nominative, genitive, dative, accusative, instrumental, prepositional.\n'
            f'Example format: {json.dumps(example)}'
        )


def parse_case_response(s: str) -> dict[str, RuDeclension]:
    return {k: RuDeclension[v.upper()] for k, v in json.loads(s).items()}
