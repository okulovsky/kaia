from demos.eaglesong.common import *
from typing import *
from kaia.zoo import Waiting
from kaia.infra.tasks import TaskProcessor, SqlMultiprocTaskProcessor, TaskCycle
from kaia.eaglesong.arch import Return, Listen
from kaia.eaglesong.telegram import TgUpdate, TgCommand
from kaia.eaglesong.amenities import menu
import logging
import os
import telegram

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class ProcessorData:
    def __init__(self, proc: TaskProcessor):
        self.chat_id = None
        self.proc = proc
        self.current_task = None #type: Optional[str]
        self.previous_task = None #type: Optional[str]


def output_task_result(c: Callable[[],TgUpdate], proc_data: ProcessorData):
    if proc_data.chat_id is None:
        yield Return()
    if proc_data.current_task is None:
        yield Return()
    if not proc_data.proc.is_finished(proc_data.current_task):
        yield TgCommand.mock().send_chat_action(proc_data.chat_id, action=telegram.constants.ChatAction.TYPING)
        yield Return()
    status = proc_data.proc.get_status(proc_data.current_task)
    proc_data.previous_task = proc_data.current_task
    proc_data.current_task = None
    if status.success and status.result is not None:
        yield TgCommand.mock().send_message(proc_data.chat_id, str(status.result))
    if status.failure:
        yield TgCommand.mock().send_message(proc_data.chat_id, status.error['value'])
    yield Return()


def get_text(proc_data):
    result = []
    task_id = proc_data.current_task
    if task_id is None:
        result.append("No current task")
        task_id = proc_data.previous_task
    if task_id is None:
        result.append('No previous task')
    else:
        status = proc_data.proc.get_status(task_id)
        result.append(f'Status: {status.status()}')
        result.append(f'Progress: {status.progress}')
        if status.error is not None:
            result.append(f'Error: {status.error}')
        result.extend(status.log)

    return '\n\n'.join(result)


def abort_task(c, proc_data):
    proc_data.proc.abort_task(proc_data.current_task)
    yield Return()


def build_menu(proc_data: ProcessorData):
    main = menu.TextMenuItem(
        'Jobs control',
        lambda: get_text(proc_data),
        2,
        add_back_button=False,
        add_reload_button=True,
        add_close_button=True
    )
    main.add_child(menu.MenuItemOverRoutine('Abort', FunctionalSubroutine(abort_task, proc_data), False))
    return main

def main(c: Callable[[], TgUpdate], proc_data: ProcessorData):
    proc_data.chat_id = c().chat_id
    yield TgCommand.mock().send_message(c().chat_id, 'Enter number N to start a task that takes N seconds. At any time, use /status to control the task.')
    while(True):
        yield Listen()
        if c().update.message.text == '/status':
            menu = build_menu(proc_data)
            yield menu
            continue
        if proc_data.current_task is not None:
            yield TgCommand.mock().send_message(c().chat_id, 'There is already task running')
            continue
        proc_data.current_task = proc_data.proc.create_task(dict(ticks=c().update.message.text))


if __name__ == '__main__':
    waiting = Waiting(1)
    cycle = TaskCycle(waiting)
    proc = SqlMultiprocTaskProcessor(cycle)
    proc.activate()
    proc_data = ProcessorData(proc)

    run_with_timer(
        FunctionalSubroutine(main, proc_data),
        FunctionalSubroutine(output_task_result, proc_data)
    )