from typing import *
from ..kaia import IKaiaSkill, KaiaAssistant, AssistantHistoryItem, TimerTick
from .scheduled_time import ScheduledTime
from dataclasses import dataclass
from kaia.dub.core import Template, Utterance
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


@dataclass
class ByTheWayTriggerArgument:
    latest_first_history: Iterable[AssistantHistoryItem]
    current_time: datetime
    last_reacted_time: Optional[datetime]

class IByTheWayTrigger(ABC):
    @abstractmethod
    def is_triggered(self, arg: ByTheWayTriggerArgument) -> bool:
        pass


@dataclass
class ByTheWayIntentTrigger(IByTheWayTrigger):
    intents: tuple[Template,...]
    delay_in_seconds: int

    def __post_init__(self):
        if isinstance(self.intents, Template):
            self.intents = (self.intents,)
        if not isinstance(self.intents, tuple):
            raise ValueError(f"Expected tuple, was {self.intents}")


    def is_triggered(self, arg: ByTheWayTriggerArgument) -> bool:
        for item_index, item in enumerate(arg.latest_first_history):
            if arg.last_reacted_time is not None and item.timestamp <= arg.last_reacted_time:
                return False
            if isinstance(item.message, TimerTick):
                continue
            if not isinstance(item.message, Utterance):
                return False
            for template in self.intents:
                if item.message.template.name == template.name:
                    delta = (arg.current_time - item.last_interation_timestamp).total_seconds()
                    if delta >= self.delay_in_seconds:
                        return True
            return False
        return False

@dataclass
class ByTheWayNotification:
    appropriate_time: ScheduledTime
    triggers: tuple[IByTheWayTrigger,...]
    output: Any
    cooldown_in_hours: int
    last_time_called: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.triggers, IByTheWayTrigger):
            self.triggers=(self.triggers,)
        if not isinstance(self.triggers, tuple):
            raise ValueError(f"Expected tuple, was {self.triggers}")



class ByTheWaySkill(IKaiaSkill):
    def __init__(self,
                 notifications: Iterable[ByTheWayNotification],
                 datetime_factory: Callable[[], datetime] = datetime.now
                 ):
        self.notifications = tuple(notifications)
        self.datetime_factory = datetime_factory
        self.last_called_time: Optional[datetime] = None
        self.current_time: Optional[datetime] = None
        self.assistant: Optional[KaiaAssistant] = None
        self.last_reacted_time: Optional[datetime] = None

    def _find_notification(self) -> Optional[ByTheWayNotification]:
        trigger_arg = ByTheWayTriggerArgument(list(reversed(self.assistant.history)), self.current_time, self.last_reacted_time)
        for notification_index, notification in enumerate(self.notifications):
            if not notification.appropriate_time.intersects_with_interval(self.last_called_time, self.current_time):
                continue

            is_triggered = False
            for trigger_index, trigger in enumerate(notification.triggers):
                triggered = trigger.is_triggered(trigger_arg)
                if triggered:
                    is_triggered = True
                    break
            if not is_triggered:
                continue
            if notification.last_time_called is None:
                return notification
            if (self.current_time - notification.last_time_called).total_seconds()/3600 >= notification.cooldown_in_hours:
                return notification


        return None


    def should_start(self, input) -> False:
        if not isinstance(input, TimerTick):
            return False

        if self.last_called_time is None:
            self.last_called_time = self.datetime_factory() - timedelta(seconds=1)
            self.current_time = self.datetime_factory()
        else:
            self.last_called_time = self.current_time
            self.current_time = self.datetime_factory()

        notification = self._find_notification()
        return notification is not None


    def should_proceed(self, input) -> False:
        return False


    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine

    def get_name(self) -> str:
        return 'ByTheWay'

    def get_runner(self):
        return self.run

    def run(self):
        notification = self._find_notification()
        notification.last_time_called = self.current_time
        self.last_reacted_time = self.current_time
        yield notification.output


    def get_replies(self) -> Iterable[Template]:
        result = []
        for notification in self.notifications:
            if isinstance(notification.output, Utterance):
                result.append(notification.output.template)
        return result




