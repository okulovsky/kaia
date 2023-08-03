from typing import *
from .subroutines import RoutineBase, Routine, Context
from dataclasses import dataclass
from typing import Generic, TypeVar
from abc import ABC, abstractmethod

class ContextTranslator(ABC):
    @abstractmethod
    def create_inner_context(self, outer_context):
        pass

    @abstractmethod
    def update_inner_context(self, outer_context, inner_context):
        pass

TInnerContext = TypeVar('TInnerContext')
TOuterContext = TypeVar('TOuterContext')

@dataclass
class TranslationContext(Context, Generic[TInnerContext, TOuterContext]):
    inner_context: TInnerContext
    outer_context: TOuterContext
    inner_message: Any

    def set_input(self, input):
        pass

    def get_input(self):
        raise NotImplementedError()


class TranslationFilter(Routine):
    def __init__(self,
                 inner_subroutine: RoutineBase,
                 context_translator: ContextTranslator,
                 command_translator: RoutineBase):
        self.inner_subroutine = inner_subroutine
        self.context_translator = context_translator
        self.command_translator = command_translator


    def run(self, outer_context):
        inner_context = self.context_translator.create_inner_context(outer_context)
        self.context_translator.update_inner_context(outer_context, inner_context)
        for command in self.inner_subroutine.instantiate(inner_context):
            translation_context = TranslationContext(inner_context, outer_context, command)
            for translated_command in self.command_translator.instantiate(translation_context):
                yield translated_command
                self.context_translator.update_inner_context(outer_context, inner_context)



