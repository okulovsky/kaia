from __future__ import annotations
from foundation_kaia.prompters import Address
from .steps import LLMRequestStep
from typing import Any, Callable

class LLMRequestApplicator:
    def __init__(self, steps: tuple[LLMRequestStep,...]):
        self.parser: Callable[[Any, str], Any]|None = None
        self.divider: Callable[[str], list]|None = None
        self.application_addresses = []

        for step in steps:
            step_parser = step.get_parser()
            if step_parser is not None:
                if self.parser is not None:
                    raise ValueError("Parser is ambiguous")
                self.parser = step_parser

            step_divider = step.get_divider()
            if step_divider is not None:
                if self.divider is not None:
                    raise ValueError("Divider is ambiguous")
                self.divider = step_divider

            step_assignment = step.get_assignment_address()
            if step_assignment is not None:
                self.application_addresses.append(Address.parse(step_assignment))

    def postprocess_output(self, case: Any, output: str) -> Any:
        if self.parser is not None:
            result = self.parser(case, output)
        else:
            result = output
        for address in self.application_addresses:
            address.set(case, result)
        return result