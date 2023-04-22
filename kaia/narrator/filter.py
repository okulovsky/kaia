from typing import *
from .core import NarrationCommand, NarrationStage, NarrationHistoryItem, Narrator
from ..eaglesong.core import BotContext, RoutineBase, TranslationFilter, Routine, TranslationContext, ContextTranslator, PushdownFilter
from dataclasses import dataclass, field

@dataclass
class NarrationContext(BotContext):
    stage: NarrationStage = field(default_factory=lambda: NarrationStage())

    def narrator(self) -> Narrator:
        return Narrator(self.stage)


class NarrationCommandTranslator(Routine):
    def __init__(self,
                 narration_translation_routine_factory: Callable[[NarrationCommand], RoutineBase],
                 ):
        self.narration_translation_routine_factory = narration_translation_routine_factory

    def run(self, context: TranslationContext):
        stage = context.inner_context.stage #type: NarrationStage
        stage.history.append(NarrationHistoryItem(True, stage.bot, context.inner_message))
        if isinstance(context.inner_message, NarrationCommand):
            yield self.narration_translation_routine_factory(context.inner_message)
        else:
            yield context.inner_message


class DefaultNarrationCommandTranslator(Routine):
    def __init__(self, message: NarrationCommand):
        self.message = message

    def run(self, context):
        yield self.message.as_plain_text()


class NarrationContextTranslator(ContextTranslator):
    def __init__(self, profile_source: Optional[Callable[[Any], Any]] = None):
        self.profile_source = profile_source

    def create_inner_context(self, outer_context):
        inner_context = NarrationContext(**outer_context.__dict__)
        if self.profile_source is None:
            inner_context.stage.user = str(outer_context.user_id)
        else:
            inner_context.stage.user = self.profile_source(outer_context.user_id)
        inner_context.stage.bot = 'kaia'
        return inner_context

    def update_inner_context(self, outer_context: BotContext, inner_context: NarrationContext):
        inner_context.set_input(outer_context.input)


class NarrationFilter(TranslationFilter):
    def __init__(self, inner_subroutine, context_translator, command_translator):
        super(NarrationFilter, self).__init__(inner_subroutine, context_translator, command_translator)

    @staticmethod
    def define(profile_source: Optional[Callable[[Any], Any]] = None,
               narration_command_translator_factory = None
               ):
        context_translator = NarrationContextTranslator(profile_source)
        if narration_command_translator_factory is None:
            narration_command_translator_factory = DefaultNarrationCommandTranslator
        command_translator = NarrationCommandTranslator(narration_command_translator_factory)
        return lambda inner_subroutine: NarrationFilter(inner_subroutine, context_translator, command_translator)






