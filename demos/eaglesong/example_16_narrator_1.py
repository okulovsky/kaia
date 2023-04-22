"""
Here we use `Narrator` class with the default `Dispatcher`. In this setup,
the narration commands are not triggering any jobs and just are printed with label.

Nevertheless, the code for the chatflow is exactly the same as for the case when jobs are triggered.
This way they are way easier to test (compare unit tests for this and the next version of this chatbot).
"""
from demos.eaglesong.common import *
from kaia.narrator import SimpleNarrationDispatcher, NarrationContext
from kaia.eaglesong.amenities.task_filter import TaskFilter


def main(context: NarrationContext):
    yield context.narrator().improvise('Say something and I will support the conversation!')
    while True:
        yield Listen()
        yield context.narrator().answer(context.input)


bot = Bot("narrator1",proc_factory =
          lambda proc: Routine.interpretable(
                SimpleNarrationDispatcher(main),
                PushdownFilter,
                TaskFilter.with_processor(proc)
          ),
          timer=True)

if __name__ == '__main__':
    run(bot)