from . import rhasspy_nlu
from ..core.algorithms.to_ini import IniRuleRecord, IniRule
from yo_fluq import Query

def _content_to_ini(rec: IniRuleRecord):
    result = []
    for c in rec.content:
        if c.constant is not None:
            v = rhasspy_nlu.escape_for_rhasspy(c.constant)
            result.append(v)
        elif c.variable is not None:
            result.append(f'<{c.variable}>{{{c.variable}}}')
        elif c.alternatives is not None:
            result.append('(' + '|'.join(c.alternatives) + ')')
        else:
            raise ValueError('Empty content item')
    return ''.join(result)


def _content_to_sample_string(rec: IniRuleRecord, values):
    result = []
    for c in rec.content:
        if c.constant is not None:
            result.append(c.constant)
        elif c.variable is not None:
            result.append(values[c.variable])
        elif c.alternatives is not None:
            result.append(c.alternatives[0])
        else:
            raise ValueError('Empty content item')
    return ''.join(result)



def rule_to_section(rule: IniRule, intent_name):
    records = []
    records.append(f'[{intent_name}]')
    headers = Query.en(rule.records).select_many(lambda z: z.headers.items()).distinct(lambda z: z[0]).to_list()
    for key, values in headers:
        records.append(f'{key} = {"|".join(values)}')
    contents = Query.en(rule.records).select(lambda z: _content_to_ini(z)).distinct().to_list()
    records.extend(contents)
    return '\n'.join(records)

def rule_to_sample_str(rule: IniRule, values):
    key = tuple(sorted(values))
    for rec in rule.records:
        if key == rec.var_code:
            c = _content_to_sample_string(rec, values)
            return c
    raise ValueError(f"Could not find a rule with variables {key}")