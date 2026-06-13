from grammatron import VariableDub
from grammatron.dubs.core.dub import IDub


def generate_values_for_dub(dub: IDub, n: int) -> list:
    return dub.generate_random_values(n)


def generate_values_for_variables(variables: list[VariableDub], n: int) -> list[dict]:
    var_dubs = {
        item.name: item.dub
        for item in variables
    }

    if not var_dubs:
        return []

    value_lists = {name: generate_values_for_dub(dub, n) for name, dub in var_dubs.items()}
    n_actual = min(len(vals) for vals in value_lists.values())
    return [{name: vals[i] for name, vals in value_lists.items()} for i in range(n_actual)]
