from datetime import timedelta
from ..core import TemplateDub, TemplateVariable, ListDub
from .int_dub import CardinalDub
from .plural_agreement import PluralAgreement
from yo_fluq import *

def make_sequence(vars: list[TemplateVariable]):
    s = [f'{v} {PluralAgreement(v.name).as_variable()}' for v in reversed(vars)]
    return ListDub.compose_string(s, ', ', ' and ')

class TimedeltaDub(TemplateDub):
    def __init__(self,
                 add_hours: bool = True,
                 add_minutes: bool = True,
                 add_seconds: bool = True,
                 ):
        if add_hours and not add_minutes and add_seconds:
            raise ValueError("True-False-True is not acceptable")
        if not add_hours and not add_minutes and not add_seconds:
            raise ValueError("At least one of hours, minutes, seconds must be added")

        self.adds = [add_seconds, add_minutes, add_hours]
        self.vars = [
            CardinalDub(120).as_variable('seconds'),
            CardinalDub(120).as_variable('minutes'),
            CardinalDub(24).as_variable('hours')
        ]
        sequences = []

        for option in Query.combinatorics.cartesian(*([[True,False]]*3)):
            if sum(option)==0:
                continue
            take_vars = []
            bad_option = False

            for i in range(3):
                if option[i] and not self.adds[i]:
                    bad_option = True
                    break
                if option[i]:
                    take_vars.append(self.vars[i])

            if bad_option:
                continue

            sequences.append(make_sequence(take_vars))

        super().__init__(*sequences)


    def variables_to_value(self, variables: dict[str, Any]) -> Any:
        seconds = variables.get('seconds', 0)
        seconds += variables.get('minutes',0) * 60
        seconds += variables.get('hours', 0) * 3600
        return timedelta(seconds=seconds)

    def value_to_variables(self, value: Any) ->dict[str,Any]:
        seconds = int(value.total_seconds())
        values = [seconds%60, (seconds//60)%60, (seconds//3600)]

        for i in range(3):
            if not self.adds[i]:
                values[i] = None
            else:
                break

        multiplies = [1, 60, 60]
        for i in range(2,0, -1):
            if not self.adds[i]:
                values[i-1] += values[i]*multiplies[i]
                values[i] = None
            else:
                break

        not_null = sum(v is not None for v in values)
        for i in range(2,-1,-1):
            if not_null == 1:
                break
            if values[i] is not None and values[i] == 0:
                values[i] = None
                not_null-=1

        result = {self.vars[i].name:values[i] for i in range(3) if values[i] is not None}
        #print(self.adds, result)
        return result

























