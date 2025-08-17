from typing import *
import types, inspect
from .rule import Rule
from .binding_settings import BindingSettings
from .service import IService
from .rule_creator import RuleCreator, MessageHandlerAttributes, SyncCallSpec
from ..stream import IMessage, Confirmation

class MessageHandlerWithCall():
    def __init__(self):
        self.calls = []

    def with_call(self, argument_type: type[IMessage], returned_type: type[IMessage] = Confirmation) -> 'MessageHandlerWithCall':
        self.calls.append(SyncCallSpec(argument_type, returned_type))
        return self

    def __call__(self, func):
        attrs = MessageHandlerAttributes(tuple(self.calls))
        setattr(func, "_message_handler", attrs)
        return func



class MessageHandlerHolder:
    def __call__(self, func):
        attrs = MessageHandlerAttributes(())
        setattr(func, "_message_handler", attrs)
        return func

    def with_call(self, argument_type: type[IMessage], returned_type: type[IMessage] = Confirmation):
        return MessageHandlerWithCall().with_call(argument_type, returned_type)


message_handler = MessageHandlerHolder()

class RulesCollection:
    def __init__(self):
        self.rules: list[Rule] = []

    def _add(self, method: Callable, settings: BindingSettings, attr: MessageHandlerAttributes):
        creator = RuleCreator(method, settings, attr)
        self.rules.append(creator.get_rule())

    def bind(self, obj: Any, settings: BindingSettings | None = None):
        if settings is None:
            if isinstance(obj, IService):
                settings = obj.binding_settings
            else:
                settings = BindingSettings()
        if callable(obj):
            self._add(obj, settings, MessageHandlerAttributes(()))
            return self

        success = 0
        for name, member in inspect.getmembers(obj):
            attr = getattr(member, "_message_handler", None)
            if attr is not None:
                self._add(member, settings, attr)
                success+=1

        if success == 0:
            raise ValueError(f"No methods with @message_handler are found in {type(obj).__name__}")

        return self







