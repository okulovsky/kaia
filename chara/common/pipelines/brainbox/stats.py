from dataclasses import dataclass
from typing import TypeVar, Generic, Any
from brainbox import BrainBox





@dataclass
class BrainBoxStats:
    cases_total: int = 0
    cases_missing_from_brainbox: int = 0
    cases_with_brainbox_errors: int = 0
    cases_with_divider_errors: int = 0
    cases_success: int = 0

    options_total: int = 0
    options_with_errors: int = 0
    options_success: int = 0

    def validate(self, success_rate: float):
        if self.cases_total == 0:
            raise ValueError("No cases")

        if self.cases_success / self.cases_total < success_rate:
            raise ValueError(f"Too few successes ({self.cases_success} / {self.cases_total}), required {success_rate}")

        if self.options_total == 0:
            raise ValueError("No options")

        if self.options_success / self.options_total < success_rate:
            raise ValueError(f"Too few options ({self.options_success} / {self.options_total}), required {success_rate}")



