"""
The following code demonstrates how the chatflow can interract with the asynchronous job.

"""
from demos.eaglesong.common import *
from kaia.infra.tasks import TaskProcessor, SqlSubprocTaskProcessor, SubprocessConfig
from kaia.eaglesong.amenities.dispatcher import Dispatcher
from kaia.eaglesong.amenities.menu import MenuFolder, FunctionalMenuItem

class StatusMenu(MenuFolder):
    def __init__(self, processor: TaskProcessor, task_id):
        self.processor = processor
        self.task_id = task_id
        super(StatusMenu, self).__init__(self.get_status_text, add_reload_button=True)
        self.items(FunctionalMenuItem('Abort', self.abort_task, False))

    def get_status_text(self):
        result = []
        caption = self.task_id
        result.append(caption)
        status = self.processor.get_status(self.task_id)
        result.append(f'Status: {status.status()}')
        result.append(f'Progress: {status.progress}')
        if status.error is not None:
            result.append(f'Error: {status.error}')
        result.extend(status.log)
        return '\n\n'.join(result)

    def abort_task(self, context):
        self.processor.abort_task(self.task_id)
        yield Return()


class TimerBot(Dispatcher):
    def __init__(self, processor: TaskProcessor):
        super(TimerBot, self).__init__()
        self.add_skill('main', PushdownFilter(Routine.ensure(self.main)))
        self.add_skill('status', PushdownFilter(Routine.ensure(self.status)))
        self.add_skill('timer', PushdownFilter(Routine.ensure(self.timer)))

        self.processor = processor
        self.current_task_id = None
        self.previous_task_id = None

    def main(self, context: BotContext):
        yield 'Enter number N to start a task that takes N seconds. At any time, use /status to control the task.'
        while True:
            yield Listen()
            if self.current_task_id is not None:
                yield f'Task is already running (id {self.current_task_id})'
            else:
                self.current_task_id = self.processor.create_task(dict(ticks=context.input))
                yield f'Task with id {self.current_task_id} has been created'


    def status(self, context):
        if self.current_task_id is not None:
            yield StatusMenu(self.processor, self.current_task_id)
        elif self.previous_task_id is not None:
            yield StatusMenu(self.processor, self.previous_task_id)
        else:
            print('no tasks')
            yield 'No task runs yet'


    def timer(self, context: BotContext):
        if self.current_task_id is None:
            yield Return()
        if not self.processor.is_finished(self.current_task_id):
            yield IsThinking()
            yield Return()
        status = self.processor.get_status(self.current_task_id)
        self.previous_task_id = self.current_task_id
        self.current_task_id = None
        if status.success and status.result is not None:
            yield status.result
        if status.failure:
            yield status.error['value']
        yield Return()


    def dispatch(self, context: BotContext):
        if isinstance(context.input, TimerTick):
            return 'timer'
        elif isinstance(context.input, SelectedOption):
            return 'status'
        elif isinstance(context.input, str) and context.input== '/status':
            if 'status' in self.active_skills:
                del self.active_skills['status']
            return 'status'
        else:
            return 'main'


bot = Bot(
    "task1",
    proc_factory=lambda proc:
        Routine.interpretable(
            TimerBot(proc),
            PushdownFilter
        ),
    timer = True
)


if __name__ == '__main__':
    bot.processor = SqlSubprocTaskProcessor(SubprocessConfig(
        'kaia.infra.tasks:Waiting',
        [1]
    ))
    bot.processor.activate()
    run(bot)