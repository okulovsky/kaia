from grammatron import Template
from dataclasses import dataclass


@dataclass
class GrammarCorrectionCase:
    template: Template
    grammar_model: GrammarModel|None = None
    grammar_reply: Any = None
    status: CaseStatus = CaseStatus.not_started
    error: str|None = None
