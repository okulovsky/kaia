from typing import *
from .rule_collection_utils import get_single_argument_type, get_annotated_output_type
import types, inspect
from .rule import Rule, RuleConnector
from dataclasses import dataclass

def build_connector(handler, publisher: str|None):
    argument = get_single_argument_type(handler)
    return RuleConnector(argument, publisher)


def build_rule(
        handler: Any,
        is_asynchronous = False,
        input: Union[Type, str, Rule, RuleConnector, None] = None,
        outputs: Optional[Tuple[Type,...]] = None,
        custom_host_name: str|None = None
        ):
    if isinstance(handler, types.MethodType):
        host = handler.__self__
    elif not inspect.isfunction(handler) and hasattr(handler,'__call__'):
        host = handler
        handler = handler.__call__
    else:
        host = None

    if input is None:
        connector = build_connector(handler, None)
    elif isinstance(input, str):
        connector = build_connector(handler, input)
    elif isinstance(input, Rule):
        connector = build_connector(handler, input.name)
    elif isinstance(input, type):
        connector = RuleConnector(input, None)
    elif isinstance(input, RuleConnector):
        connector = input
    else:
        raise ValueError(f"Unexpected value for input: {input}")

    if outputs is None:
        outputs = get_annotated_output_type(handler)

    if outputs is not None:
        outputs = tuple(outputs)

    host_name = custom_host_name
    if host_name is None:
        if host is None:
            host_name = '#'
        else:
            host_name = type(host).__name__

    full_name = host_name+'/'+handler.__name__

    return Rule(
        full_name,
        connector,
        host,
        handler,
        is_asynchronous,
        outputs,
    )

def message_handler(func):
    setattr(func, "_is_message_handler", True)
    return func

class RulesCollection:
    def __init__(self):
        self.rules: list[Rule] = []

    def add(self,
            handler: Callable,
            input: Union[Type, str, Rule, RuleConnector, None] = None,
            is_asynchronous: bool = False,
            outputs:Optional[Tuple[Type,...]] = None,
            custom_host_name: str|None = None
            ) -> 'Rule':
        rule = build_rule(handler, is_asynchronous, input, outputs, custom_host_name)
        self.rules.append(rule)
        return rule


    def bind(self, obj: Any, custom_host_name: str|None = None):
        if callable(obj):
            self.add(obj, custom_host_name=custom_host_name)
            return self
        handlers = []
        for name, member in inspect.getmembers(obj):
            if callable(member) and getattr(member, "_is_message_handler", False):
                handlers.append(member)
        if len(handlers) == 0:
            raise ValueError("No methods with @message_handler: have you forgot to add decorator?")
        for handler in handlers:
            self.add(handler, custom_host_name=custom_host_name)
        return self







