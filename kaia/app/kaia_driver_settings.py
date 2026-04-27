from typing import Any

from kaia import KaiaDriver, KaiaContext, KaiaAssistant, IKaiaSkill, skills, StateTranslator, IAssistantFactory
from pathlib import Path
from yo_fluq import FileIO
from avatar.daemon import ChatCommand, SoundCommand, TextEvent, ButtonPressedEvent, TickEvent, InitializationEvent, UserWalkInService
from .app import KaiaApp, IAppInitializer
from dataclasses import dataclass
from grammatron import Template, TemplatesCollection
from avatar.app import AvatarApi
from .avatar_daemon_app_settings import CHARACTERS



class AssistantFactory(IAssistantFactory):
    def __init__(self, avatar_api: AvatarApi):
        self.avatar_api = avatar_api
        self.notification_registers = []
        self.skills = []

        self.timer_register = None

    def create_timer_register(self):
        if self.avatar_api is not None:
            self.avatar_api.cache.upload(
                'alarm.wav',
                FileIO.read_bytes(Path(__file__).parent / 'files/alarm.wav'),
            )
        timer_register = skills.NotificationRegister(
            (SoundCommand('alarm.wav'), ChatCommand("alarm ringing", ChatCommand.MessageType.system)),
            (ChatCommand("alarm stopped", ChatCommand.MessageType.system),)
        )
        self.notification_registers.append(timer_register)
        return timer_register

    def create_common_skills(self):
        self.skills.append(skills.EchoSkill())
        self.skills.append(skills.PingSkill())

        self.skills.append(skills.DateSkill())
        self.skills.append(skills.TimeSkill())

        self.skills.append(skills.LogFeedbackSkill())

        self.timer_register = self.create_timer_register()
        self.skills.append(skills.TimerSkill(self.timer_register))

        self.skills.append(skills.VolumeSkill(0.2))

        self.skills.append(skills.ChangeImageSkill())
        self.skills.append(skills.ActivitySkill())

    def create_specific_skills(self):
        self.skills.append(skills.CookBookSkill(
            self.timer_register,
            [skills.Recipe.define(
                'tea',
                "Boil water",
                "Put a teabag in the water",
                { 1: "Enjoy your tea" }
            )]
        ))
        self.skills.append(skills.ChangeCharacterSkill(CHARACTERS))

    def create_system_skills(self):
        self.skills.append(skills.NotificationSkill(
            self.notification_registers,
            pause_between_alarms_in_seconds=10,
            volume_delta=0.2
        ))
        self.skills.append(help := skills.HelpSkill())
        help.skills = self.skills



    def create_assistant(self, context: KaiaContext):
        self.create_common_skills()
        self.create_specific_skills()
        self.create_system_skills()

        assistant = KaiaAssistant(self.skills)
        assistant.raise_exceptions = False
        help.assistant = assistant

        return assistant

    def wrap_assistant(self, assistant: KaiaAssistant) -> Any:
        assistant = StateTranslator(assistant)
        return assistant


@dataclass
class KaiaDriverSettings(IAppInitializer):
    def create_client(self, app: KaiaApp):
        client = app.create_avatar_client()
        client.set_allowed_types(TextEvent, ButtonPressedEvent, TickEvent, InitializationEvent)
        return client

    def bind_app(self, app: 'KaiaApp'):
        if app.avatar_api is None:
            raise ValueError("KaiaApp.avatar_api must be set before KaiaDriverSettings.bind_app")
        if app._avatar_client is None:
            raise ValueError("KaiaApp._avatar_client must be set before KaiaDriverSettings.bind_app")

        app.kaia_driver = KaiaDriver(
            AssistantFactory(app.avatar_api),
            self.create_client(app),
            skip_logging_for_types=(TickEvent,)
        )
