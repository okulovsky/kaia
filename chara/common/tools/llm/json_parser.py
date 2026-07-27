from typing import Any
import json
import re
from foundation_kaia.marshalling import Serializer

def parse_json(s: str) -> Any:
    match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', s, re.DOTALL)
    if match:
        s = match.group(1)
    else:
        match = re.search(r'\{.*\}', s, re.DOTALL)
        if match:
            s = match.group(0)
    try:
        return json.loads(s)
    except Exception as e:
        raise Exception(f"Exception when parsing this JSON\n{s}\nfrom text\n{s}") from e


def parse_and_assign_json(field: str, t: type|None = None):
    def _(case: Any, s: str) -> None:
        value = parse_json(s)
        if t is not None:
            try:
                value = Serializer.parse(t).from_json(value)
            except Exception as e:
                raise Exception(f"Exception when parsing this JSON\n{s}\nfrom text\n{s}") from e
        setattr(case, field, value)
    return _

def parse_json_array(s: str) -> list[Any]:
    match = re.search(r'```(?:json)?\s*\n?(\[.*?\])\s*\n?```', s, re.DOTALL)
    if match:
        s = match.group(1)
    else:
        match = re.search(r'\[.*\]', s, re.DOTALL)
        if match:
            s = match.group(0)
    return json.loads(s)