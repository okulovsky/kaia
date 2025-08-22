from .binding_settings import BindingSettings, EndpointBindingSettings
from typing import Callable, Any
from dataclasses import dataclass
from .rule import Rule, RuleConnector, SyncCallSpec
from .rule_creator_utils import get_single_argument_type, get_annotated_output_type
import types



@dataclass
class MessageHandlerAttributes:
    calls: tuple[SyncCallSpec,...]

@dataclass
class RuleCreator:
    method: Callable
    settings: BindingSettings
    attributes: MessageHandlerAttributes|None

    def get_host(self):
        if isinstance(self.method, types.MethodType):
            return self.method.__self__
        else:
            return None

    def get_name(self):
        if self.get_host() is None:
            if self.settings.custom_name is not None:
                return self.settings.custom_name
            else:
                return self.method.__name__
        else:
            if self.settings.custom_name is not None:
                return self.settings.custom_name+'/'+self.method.__name__
            else:
                return type(self.get_host()).__name__+'/'+self.method.__name__

    def get_connector(self):
        input_type = get_single_argument_type(self.method)
        setting = self.settings.get_setting_for_method(self.method)
        if setting is None:
            setting = self.settings.get_setting_for_type(input_type)
        if setting is None:
            include = exclude = None
        else:
            include = EndpointBindingSettings.normalize(setting.include_senders)
            exclude = EndpointBindingSettings.normalize(setting.exclude_senders)
        return RuleConnector(input_type, include, exclude)

    def get_rule(self):
        if self.attributes is None:
            self.attributes = MessageHandlerAttributes()

        return Rule(
            self.get_name(),
            self.get_connector(),
            self.get_host(),
            self.method,
            self.settings.is_asynchronous,
            get_annotated_output_type(self.method),
            self.attributes.calls
        )
