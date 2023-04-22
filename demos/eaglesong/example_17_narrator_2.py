"""
Here we finally achieve the goal of the chatbot that has a simple and readable chatflow
and at the same time is integrated with the jobs. The chatflow is exactly as in previous
narrator example, but it's now augmented with the different `NarrationCommandTranslator`:
for each command, the Task is triggered, then waited for, and then its output is used to
modify the input. Yes, for now it's just waiting task and string concatenation,
but hopefully one can see where it's coming to.
"""
from demos.eaglesong.common import *
from kaia.narrator import NarrationCommand, SimpleNarrationDispatcher
from kaia.eaglesong.amenities.task_filter import CreateTaskAndWait, TaskFilter
from demos.eaglesong.example_16_narrator_1 import main
from kaia.infra.tasks import SqlSubprocTaskProcessor, SubprocessConfig


class NarrationCommandTranslator(Routine):
    def __init__(self, command: NarrationCommand):
        self.command = command

    def run(self, context: BotContext):
        yield CreateTaskAndWait(dict(ticks=2))
        result = context.input
        yield f"{self.command.query} ({self.command.type.name}, {result.result} sec)"


bot = Bot("narrator1",proc_factory =
          lambda proc: Routine.interpretable(
                SimpleNarrationDispatcher(main, narration_command_translator_factory=NarrationCommandTranslator),
                PushdownFilter,
                TaskFilter.with_processor(proc)
          ),
          timer=True)

if __name__ == '__main__':
    bot.processor = SqlSubprocTaskProcessor(SubprocessConfig(
        'kaia.infra.tasks:Waiting',
        [1]
    ))
    bot.processor.activate()
    run(bot)