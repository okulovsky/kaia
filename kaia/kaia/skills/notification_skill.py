from typing import *
from kaia.kaia.core import IKaiaSkill, VolumeCommand
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from kaia.eaglesong.core import TimerTick, Return, Listen

@dataclass
class NotificationInfo:
    start: datetime
    duration: timedelta


    @property
    def end(self):
        return self.start + self.duration


@dataclass
class NotificationRegister:
    audio: Any
    audio_stop: Optional[Any] = None
    instances: Dict[str, NotificationInfo] = field(default_factory=lambda: {})


@dataclass
class FoundNotification:
    register: NotificationRegister
    name: str
    info: NotificationInfo


class NotificationSkill(IKaiaSkill):
    def __init__(self,
                 registers: Iterable[NotificationRegister],
                 current_time_factory: Callable[[], datetime] = datetime.now,
                 pause_between_alarms_in_seconds: Optional[float] = None,
                 volume_delta: Optional[float] = None
                 ):
        self.registers = tuple(registers)
        self.current_time_factory = current_time_factory
        self.pause_between_alarms_in_seconds = pause_between_alarms_in_seconds
        self.volume_delta = volume_delta

    def _find_notification(self) -> Optional[FoundNotification]:
        current_time = self.current_time_factory()
        for register in self.registers:
            for name, instance in register.instances.items():
                if instance.end <= current_time:
                    return FoundNotification(register, name, instance)
        return None

    def get_name(self) -> str:
        return 'Notification'

    def get_runner(self):
        return self.run

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine


    def should_start(self, input) -> False:
        return self._find_notification() is not None

    def should_proceed(self, input) -> False:
        return True



    def run(self):
        last_time_audio_sent: Optional[datetime] = None
        first_notification = True
        while True:
            active_notification = self._find_notification()
            if active_notification is None:
                raise Return()
            input = yield
            if isinstance(input, TimerTick):
                if (
                    self.pause_between_alarms_in_seconds is None
                    or last_time_audio_sent is None
                    or (self.current_time_factory()-last_time_audio_sent).total_seconds() >= self.pause_between_alarms_in_seconds
                ):
                    yield active_notification.register.audio
                    last_time_audio_sent = self.current_time_factory()
                    if self.volume_delta is not None:
                        stash_to = 'before_notification' if first_notification else None
                        yield VolumeCommand(relative_value=self.volume_delta, stash_to = stash_to)
                    first_notification = False
                yield Listen()
            else:
                if active_notification.register.audio_stop is not None:
                    yield active_notification.register.audio_stop
                del active_notification.register.instances[active_notification.name]
                if self.volume_delta is not None and not first_notification:
                    yield VolumeCommand(restore_from='before_notification')
                raise Return()

