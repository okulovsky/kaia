from kaia import skills
from .avatar_definition import characters, WorldFields
from kaia.kaia import KaiaCoreService, KaiaCoreServiceSettings, Message, KaiaAssistant
from pathlib import Path
from brainbox import File, ControllersSetup
from .app import KaiaApp
from eaglesong.templates import *
from brainbox.deciders import Whisper, OpenTTS, RhasspyKaldi
from . import smalltalk_skill
from talents.german.quiz import GermanQuizSkill


class CommonIntents(TemplatesCollection):
    stop = Template('Stop','Cancel')


class DemoCoreService(KaiaCoreService):
    def __init__(self,
                 settings: KaiaCoreServiceSettings
                 ):
        super().__init__(settings)

    def create_skills(self):
        skills_list = []

        skills_list.append(skills.EchoSkill())
        skills_list.append(skills.PingSkill())

        skills_list.append(skills.DateSkill())
        skills_list.append(skills.TimeSkill())
        # The latitude of Alexanderplatz, Berlin, Germany is 52.521992, and the longitude is 13.413244.
        weather_settings = skills.weather.WeatherSettings(52.521992, 13.413244, 'Europe/Berlin')
        skills_list.append(skills.weather.WeatherSkill(weather_settings))
        skills_list.append(skills.JokeSkill())
        skills_list.append(skills.SmalltalkSkill(smalltalk_skill.SmalltalkInputs, smalltalk_skill.SmalltalkReply))

        timer_audio = File.read(Path(__file__).parent / 'files/sounds/alarm.wav')
        timer_audio.text = '*alarm ringing*'
        timer_register = skills.NotificationRegister(
            (timer_audio, Message(Message.Type.System, "*alarm ringing*")),
            (Message(Message.Type.System, '*alarm stopped*'),)
        )
        skills_list.append(skills.TimerSkill(timer_register))
        skills_list.append(
            skills.NotificationSkill([timer_register], pause_between_alarms_in_seconds=10, volume_delta=0.2))

        skills_list.append(skills.ChangeImageSkill())
        skills_list.append(skills.VolumeSkill(0.2))
        skills_list.append(help := skills.HelpSkill())
        skills_list.append(skills.LogFeedbackSkill())
        skills_list.append(skills.ChangeCharacterSkill(characters))
        skills_list.append(skills.InitializationSkill({WorldFields.language: 'en'}))
        skills_list.append(skills.NarrationSkill())

        skills_list.append(GermanQuizSkill.create_skill(
            Path(__file__).parent / 'files/german_quiz_words.json',
            None,
            3,
        ))
        return skills_list

    def create_assistant(self):
        assistant = KaiaAssistant(self.create_skills())
        assistant.raise_exceptions = False
        help.assistant = assistant
        assistant.additional_intents.extend(CommonIntents.get_templates())
        return assistant

def get_controller_setup():
    return ControllersSetup((
        ControllersSetup.Instance(RhasspyKaldi),
        ControllersSetup.Instance(OpenTTS),
        ControllersSetup.Instance(Whisper, None, 'base')
    ))

def set_core_service(app: KaiaApp, add_controller_setup: bool = True):
    if add_controller_setup:
        setup = get_controller_setup()
    else:
        setup = None
    settings = KaiaCoreServiceSettings(
        avatar_api=app.avatar_api,
        audio_api=app.audio_control_api,
        brainbox_api=app.brainbox_api,
        kaia_api=app.kaia_api,
        brainbox_setup=setup,
    )
    app.kaia_core = DemoCoreService(settings)

