from typing import Any
import json
import re
from foundation_kaia.marshalling import Serializer, ListHandler, NoneHandler

class Json:
    @staticmethod
    def parse_object(s: str) -> Any:
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

    @staticmethod
    def parse_array(s: str) -> list[Any]:
        match = re.search(r'```(?:json)?\s*\n?(\[.*?\])\s*\n?```', s, re.DOTALL)
        if match:
            s = match.group(1)
        else:
            match = re.search(r'\[.*\]', s, re.DOTALL)
            if match:
                s = match.group(0)
        return json.loads(s)

    @staticmethod
    def is_array(serializer: Serializer) -> bool:
        non_none = [
            (handler, declared)
            for handler, declared in zip(serializer.handlers, serializer.annotation.types)
            if not isinstance(handler, NoneHandler)
        ]
        if len(non_none) != 1:
            return False
        handler, declared = non_none[0]
        if isinstance(handler, ListHandler):
            return True
        return declared.mro[0].type in (list, tuple)
