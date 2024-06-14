from zoo.assistant import weather, joke
from kaia.kaia import skills
from .narration import characters
from .common_intents import CommonIntents
from kaia.kaia.audio_control_core_service import KaiaCoreAudioControlServiceSettings, KaiaCoreAudioControlService
from kaia.kaia.core import KaiaMessage
from pathlib import Path
from kaia.eaglesong.core import Audio

class DemoCoreService(KaiaCoreAudioControlService):
    def __init__(self,
                 settings: KaiaCoreAudioControlServiceSettings
                 ):
        super().__init__(settings)


    def create_assistant(self):
        skills_list = []

        skills_list.append(skills.EchoSkill())
        skills_list.append(skills.PingSkill())

        skills_list.append(skills.DateSkill())
        skills_list.append(skills.TimeSkill())
        # The latitude of Alexanderplatz, Berlin, Germany is 52.521992, and the longitude is 13.413244.
        skills_list.append(weather.WeatherSkill(52.521992, 13.413244, 'Europe/Berlin'))
        skills_list.append(joke.JokeSkill())

        timer_audio = Audio.from_file(Path(__file__).parent/'files/sounds/alarm.wav')
        timer_audio.text = '*alarm ringing*'
        timer_register = skills.NotificationRegister(timer_audio, KaiaMessage(True, '*alarm stopped*'))
        skills_list.append(skills.TimerSkill(timer_register))
        skills_list.append(skills.NotificationSkill([timer_register], pause_between_alarms_in_seconds=10, volume_delta=0.2))

        skills_list.append(skills.ChangeImageSkill(self.settings.avatar_api))
        skills_list.append(skills.VolumeSkill(0.2))
        skills_list.append(help:=skills.HelpSkill())
        skills_list.append(skills.LogFeedbackSkill())
        skills_list.append(skills.ChangeCharacterSkill(characters, self.settings.avatar_api))

        assistant = skills.KaiaTestAssistant(skills_list)
        assistant.raise_exceptions = False
        help.assistant = assistant
        assistant.additional_intents.extend(CommonIntents.get_templates())
        return assistant

