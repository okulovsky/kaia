from ...paraphrasing.basic_pipelines.template_paraphrasing import generate_values_for_variables, ParsedTemplate
from grammatron import Template
from dataclasses import dataclass
from typing import Any

def export_dataset(templates: list[Template]) -> list[dict]:
    result = []
    for template in templates:
        intent = template._stored_info.original_template_name
        parsed_template = ParsedTemplate.parse_single(template)
        if len(parsed_template.variables) == 0:
            result.append(dict(
                text = template.utter().to_str(),
                intent = intent,
                values = None
            ))
            continue
        values = generate_values_for_variables(parsed_template.variables, 10)
        for v in values:

            v_desc = []
            for variable in parsed_template.variables:
                v_desc.append(dict(
                    name = variable.name,
                    type = type(variable.dub).__name__,
                    value = v[variable.name]
                ))

            result.append(dict(
                text = template.utter(v).to_str(),
                intent = intent,
                values = v_desc
            ))

    return result








