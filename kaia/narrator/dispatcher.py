from typing import *
from ..eaglesong.amenities.dispatcher import Dispatcher
from ..eaglesong.core import RoutineBase, ConstantRoutine, BotContext, IBotInput, Listen
from .filter import NarrationFilter, NarrationCommand, PushdownFilter

class SimpleNarrationDispatcher(Dispatcher):
    def __init__(self,
                 head_skill: Any,
                 profile_source: Optional[Callable[[Any], Any]] = None,
                 narration_command_translator_factory: Optional[Callable[[NarrationCommand], Any]] = None,
                 ):
        super(SimpleNarrationDispatcher, self).__init__()
        narrator_definition = NarrationFilter.define(profile_source, narration_command_translator_factory)
        self.add_skill('main', RoutineBase.interpretable(head_skill, PushdownFilter, narrator_definition, PushdownFilter))
        self.add_skill('fallback', ConstantRoutine('🐱'))

    def dispatch(self, context: BotContext):
        if 'main' not in self.active_skills:
            return 'main'
        if self.active_skills['main'].expect(context.input):
            return 'main'
        last_output = self.active_skills['main'].last_output
        if isinstance(last_output, Listen) and last_output.expectation is None and IBotInput.is_content_input(context.input):
            return 'main'
        if IBotInput.is_content_input(context.input):
            return 'fallback'








