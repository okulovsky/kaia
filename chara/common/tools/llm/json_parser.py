from typing import Any
import json
import re

def parse_json(s: str) -> Any:
    match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', s, re.DOTALL)
    if match:
        s = match.group(1)
    else:
        match = re.search(r'\{.*\}', s, re.DOTALL)
        if match:
            s = match.group(0)
    return json.loads(s)