from demos.eaglesong.common import *
from demos.eaglesong.example_14_task_1 import StatusMenu
from kaia.infra.tasks import TaskProcessor, SqlSubprocTaskProcessor, SubprocessConfig, TaskResult
from kaia.eaglesong.amenities.dispatcher import Dispatcher
from kaia.eaglesong.amenities.task_filter import CreateTaskAndWait, TaskFilter



class TaskBot(Dispatcher):
    def __init__(self, processor: TaskProcessor):
        super(TaskBot, self).__init__()
        self.add_skill('talk', PushdownFilter(Routine.ensure(self.talk)))
        self.add_skill('status', PushdownFilter(Routine.ensure(self.status)))
        self.add_skill('fallback', PushdownFilter(Routine.ensure(self.fallback)))
        self.processor = processor


    def talk(self, context: BotContext):
        yield 'Enter number N to start a task that takes N seconds. At any time, use /status to control the task.'
        while True:
            yield Listen.for_types(str, int)
            ticks = context.input
            yield CreateTaskAndWait(dict(ticks=ticks))
            response = context.input #type: TaskResult
            if response.success:
                yield response.result
            else:
                yield str(response.error)


    def fallback(self, context: BotContext):
        yield 'Oops'


    def status(self, context):
        tasks = self.processor.get_active_tasks()
        if len(tasks)==0:
            yield 'No active tasks'
        else:
            yield StatusMenu(self.processor, tasks[0])


    def dispatch(self, context: BotContext):
        for name, skill in self.active_skills.items():
            if skill.expect(context.input):
                return name
        if IBotInput.is_content_input(context.input):
            if context.input == '/status':
                if 'status' in self.active_skills:
                    del self.active_skills['status']
                return 'status'
            if 'talk' not in self.active_skills:
                return 'talk'
            return 'fallback'


bot = Bot(
    "task2",
    proc_factory=lambda proc: Routine.interpretable(
        TaskBot(proc),
        PushdownFilter,
        TaskFilter.with_processor(proc)
    ),
    timer=True
)


if __name__ == '__main__':
    bot.processor = SqlSubprocTaskProcessor(SubprocessConfig(
        'kaia.infra.tasks:Waiting',
        [1]
    ))
    bot.processor.activate()
    run(bot)