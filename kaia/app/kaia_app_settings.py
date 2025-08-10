from kaia import skills
from kaia.assistant import KaiaAssistant, IKaiaSkill
from kaia.driver import KaiaDriver, DefaultKaiaInputTransformer, KaiaContext
from pathlib import Path
from yo_fluq import FileIO
from avatar.daemon import ChatCommand, SoundCommand
from .app import KaiaApp, IAppInitializer
from .avatar_processor_app_settings import characters
from dataclasses import dataclass
from grammatron import Template, TemplatesCollection
from avatar.server import AvatarApi
from loguru import logger
from avatar.daemon import STTService

class CommonIntents(TemplatesCollection):
    stop = Template('Stop','Cancel')


class AssistantFactory:
    def __init__(self, avatar_api: AvatarApi):
        self.avatar_api = avatar_api

    def create_timer_register(self):
        if self.avatar_api is not None:
            self.avatar_api.file_cache.upload(
                FileIO.read_bytes(Path(__file__).parent / 'files/alarm.wav'),
                'alarm.wav')
        timer_register = skills.NotificationRegister(
            (SoundCommand('alarm.wav'), ChatCommand("alarm ringing", ChatCommand.MessageType.system)),
            (ChatCommand("alarm stopped", ChatCommand.MessageType.system),)
        )
        return timer_register


    def create_skills(self) -> list[IKaiaSkill]:
        skills_list = []

        skills_list.append(skills.EchoSkill())
        skills_list.append(skills.PingSkill())

        skills_list.append(skills.DateSkill())
        skills_list.append(skills.TimeSkill())

        timer_register = self.create_timer_register()
        recipe_register = self.create_timer_register()
        skills_list.append(skills.TimerSkill(timer_register))
        skills_list.append(skills.NotificationSkill(
            [timer_register, recipe_register],
            pause_between_alarms_in_seconds=10,
            volume_delta=0.2
        ))
        skills_list.append(skills.CookBookSkill(
            recipe_register,
            [skills.Recipe(
                'tea',
                [
                    skills.Recipe.Stage("Boil water"),
                    skills.Recipe.Stage("Put a teabag in the water"),
                    skills.Recipe.Stage(timer_for_minutes=1),
                    skills.Recipe.Stage("Enjoy your tea"),
                ]
            )]
        ))

        skills_list.append(skills.ChangeImageSkill())
        skills_list.append(skills.VolumeSkill(0.2))
        skills_list.append(skills.LogFeedbackSkill())
        skills_list.append(skills.ChangeCharacterSkill(characters))


        return skills_list


    def create_assistant(self, context: KaiaContext):
        skills_list = self.create_skills()
        skills_list.append(help := skills.HelpSkill())
        assistant = KaiaAssistant(skills_list)
        assistant.raise_exceptions = False
        help.assistant = assistant
        assistant.additional_intents.extend(CommonIntents.get_templates())

        return assistant


@dataclass
class KaiaAppSettings(IAppInitializer):
    def bind_app(self, app: 'KaiaApp'):
        app.kaia_driver = KaiaDriver(
            AssistantFactory(app.avatar_api).create_assistant,
            app.create_avatar_client(),
            DefaultKaiaInputTransformer(True)
        )
