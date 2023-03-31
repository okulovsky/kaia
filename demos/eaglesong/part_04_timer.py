from typing import *
from kaia.eaglesong.telegram import TgCommand, TgUpdate
import datetime
from kaia.eaglesong.arch import  Listen, Subroutine
from kaia.eaglesong.amenities.menu import MenuItemOverRoutine, TextMenuItem, AbstractTelegramMenuItem
from demos.eaglesong.common import *
import requests

def on_timer(c: Callable[[], TgUpdate]):
    if len(c().bridge.chats)==1:
        for chat_id in c().bridge.chats:
            yield TgCommand.mock().send_message(chat_id, str(datetime.datetime.now()))

def main(c: Callable[[], TgUpdate]):
    yield TgCommand.mock().send_message(c().chat_id, 'This bot will send you a current datetime every second. Enter /toggle to pause/resume')
    while True:
        yield Listen()
        if c().update.message.text == '/toggle':
            job = c().bridge.application.job_queue.get_jobs_by_name('timer')
            job[0].enabled = not job[0].enabled

if __name__ == '__main__':
    run_with_timer(main, on_timer)

