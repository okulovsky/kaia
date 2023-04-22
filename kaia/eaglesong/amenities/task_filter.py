from typing import *
from ...infra.tasks import TaskProcessor, TaskResult
from ..core import Routine, RoutineBase, Listen, TimerTick, Automaton, BotContext, IsThinking, Return
from dataclasses import dataclass
from functools import partial

@dataclass
class CreateTask:
    payload: Any

class TaskFilter(Routine):
    def __init__(self, inner_subroutine: RoutineBase, processor: TaskProcessor):
        self.inner_subroutine = inner_subroutine
        self.processor = processor

    @staticmethod
    def with_processor(processor):
        return partial(TaskFilter, processor = processor)

    def process_aut(self, tasks, aut):
        while True:
            result = aut.process()
            if isinstance(result, CreateTask):
                task_id = self.processor.create_task(result.payload)
                aut.context.set_input(task_id)
                tasks.add(task_id)
            elif isinstance(result, Listen):
                break
            else:
                yield result


    def run(self, context: BotContext):
        aut = Automaton(self.inner_subroutine, context)
        tasks = set()
        while True:
            for c in self.process_aut(tasks, aut):
                yield c
            if isinstance(context.input, TimerTick):
                for task in list(tasks):
                    if self.processor.is_finished(task):
                        tasks.remove(task)
                        status = self.processor.get_status(task)
                        context.set_input(status)
                        for c in self.process_aut(tasks, aut):
                            yield c
                if len(tasks)>0:
                    yield IsThinking()
            yield Listen()


class CreateTaskAndWait(Routine):
    def __init__(self, payload):
        self.payload = payload

    def run(self, context: BotContext):
        yield CreateTask(self.payload)
        task_id = context.input
        yield Listen.for_condition(lambda z: isinstance(z, TaskResult) and z.id==task_id)
        task_result = context.input
        yield Return(task_result)




