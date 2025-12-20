from typing import *
from kaia import IKaiaSkill, TickEvent, Pushback, VolumeCommand
from avatar.daemon import VolumeControlService, IMessage
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from eaglesong.core import Return, Listen

@dataclass
class NotificationInfo:
    start: datetime
    duration: timedelta
    pushback_after: Any = None
    tags: dict[str, str] = field(default_factory=dict)
    label: str|None = None

    @property
    def end(self):
        return self.start + self.duration


@dataclass
class NotificationRegister:
    notification_signals: Tuple[IMessage,...]
    exit_signals: Optional[Tuple[IMessage,...]] = None
    instances: list[NotificationInfo] = field(default_factory=list)

@dataclass
class FoundNotification:
    register: NotificationRegister
    index: int
    info: NotificationInfo


class NotificationSkill(IKaiaSkill):
    def __init__(self,
                 registers: Iterable[NotificationRegister],
                 pause_between_alarms_in_seconds: Optional[float] = None,
                 volume_delta: Optional[float] = None
                 ):
        self.registers: tuple[NotificationRegister,...] = tuple(registers)
        self.pause_between_alarms_in_seconds = pause_between_alarms_in_seconds
        self.volume_delta = volume_delta

    def _find_notification(self, current_time) -> Optional[FoundNotification]:
        for register in self.registers:
            for index, instance in enumerate(register.instances):
                if instance.end <= current_time:
                    return FoundNotification(register, index, instance)
        return None

    def get_name(self) -> str:
        return 'Notification'

    def get_runner(self):
        return self.run

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine


    def should_start(self, input) -> bool:
        if not isinstance(input, TickEvent):
            return False
        return self._find_notification(input.time) is not None

    def should_proceed(self, input) -> bool:
        return True



    def run(self):
        last_time_audio_sent: Optional[datetime] = None
        first_notification = True

        input = yield
        active_notification = self._find_notification(input.time)
        if active_notification is None:
            raise Return()

        while True:
            input = yield
            if isinstance(input, TickEvent):
                current_time = input.time
                if (
                    self.pause_between_alarms_in_seconds is None
                    or last_time_audio_sent is None
                    or (current_time-last_time_audio_sent).total_seconds() >= self.pause_between_alarms_in_seconds
                ):
                    for item in active_notification.register.notification_signals:
                        yield item.with_new_envelop()
                    last_time_audio_sent = current_time
                    if self.volume_delta is not None:
                        stash_to = 'before_notification' if first_notification else None
                        yield VolumeControlService.Command(relative_value=self.volume_delta, stash_to = stash_to)
                    first_notification = False
                yield Listen()
            else:
                if active_notification.register.exit_signals is not None:
                    for item in active_notification.register.exit_signals:
                        yield item.with_new_envelop()
                del active_notification.register.instances[active_notification.index]
                if self.volume_delta is not None and not first_notification:
                    yield VolumeControlService.Command(restore_from='before_notification')
                if active_notification.info.pushback_after is not None:
                    raise Return(Pushback(active_notification.info.pushback_after))
                else:
                    raise Return()

