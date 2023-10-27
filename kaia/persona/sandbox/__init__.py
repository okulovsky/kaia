from .date import DateSkill, DateIntents, DateReplies, Weekdays
from .time import TimeSkill, TimeIntents, TimeReplies
from .assistant import HomeAssistant
from .common_replies import CommonReplies

def create_sandbox_assistant():
    return HomeAssistant([DateSkill(), TimeSkill()])