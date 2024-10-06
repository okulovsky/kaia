from unittest import TestCase
from kaia.brainbox import BrainBoxApi, BrainBoxTask
from kaia.avatar import AvatarApi, AvatarSettings, RecognitionSettings
from kaia.brainbox.utils import TestSpeaker
from kaia.brainbox.deciders import (
    Resemblyzer,
    RhasspyKaldiInstaller, RhasspyKaldiSettings,
    OpenTTSInstaller, OpenTTSSettings,
    ResemblyzerInstaller, ResemblyzerSettings,
    Collector,
    WhisperInstaller, WhisperSettings
)
from kaia.dub import Template, TemplatesCollection, IntentsPack
from kaia.brainbox import MediaLibrary
from kaia.infra import Loc
from kaia.narrator import World
from yo_fluq_ds import *

class Templates(TemplatesCollection):
    how_are_you = Template("How are you?")

resemblyzer_installer = ResemblyzerInstaller(ResemblyzerSettings())
resemblyzer_model = 'avatar_test'

class RecognitionTestCase(TestCase):
    def check_files(self, *files):
        dataset_path = resemblyzer_installer.resource_folder('datasets', resemblyzer_model)
        file_list = (
            Query.folder(dataset_path, '**/*.wav')
            .select(lambda z: str(z.relative_to(dataset_path)))
            .to_set()
        )
        self.assertSetEqual(set(files), file_list)


    def test_recognition(self):
        services = dict(
            OpenTTS = OpenTTSInstaller(OpenTTSSettings()),
            RhasspyKaldi = RhasspyKaldiInstaller(RhasspyKaldiSettings()),
            Resemblyzer = resemblyzer_installer,
            Collector = Collector(),
            Whisper = WhisperInstaller(WhisperSettings())
        )

        with BrainBoxApi.Test(services, always_on_planner=True) as bb_api:
            speaker = TestSpeaker(bb_api, remake_everything=True)
            with AvatarApi.Test(AvatarSettings(brain_box_api=bb_api, resemblyzer_model_name=resemblyzer_model)) as av_api:
                with Loc.create_temp_file('avatar_recognition_test_media_library','zip') as media_library_path:
                    #Training Resemblyzer model
                    records = []
                    for i in range(2):
                        fname = speaker.speak('Hello, world!', i)
                        records.append(MediaLibrary.Record(
                            fname,
                            bb_api.cache_folder,
                            tags = dict(split='train', speaker=str(i))
                        ))
                    lib = MediaLibrary(tuple(records))
                    lib.save(media_library_path)
                    av_api.recognition_speaker_train(media_library_path)

                    #Checking that dataset is what is expected
                    self.check_files('train/0/'+records[0].filename, 'train/1/'+records[1].filename)

                    #Training Kaldi model
                    rhasspy_model = 'avatar_rec_test'
                    av_api.recognition_train((IntentsPack(rhasspy_model, tuple(Templates.get_templates())),), ())

                    #Setting up initial avatar state
                    av_api.state_change({World.user.field_name: '1'})
                    self.assertEqual('1', av_api.state_get()[World.user.field_name])

                    #Feeding the sample from speaker 0
                    test_0 = speaker.speak(Templates.how_are_you().to_str())
                    utterance_0 = av_api.recognition_transcribe(
                        test_0,
                        RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model=rhasspy_model)
                    )
                    self.assertIn(utterance_0, Templates.how_are_you)
                    self.assertEqual('0', av_api.state_get()[World.user.field_name])

                    #Feeding the sample from speaker 1
                    message = "Hello"
                    test_1 = speaker.speak(message, 1)
                    utterance_1 = av_api.recognition_transcribe(
                        test_1,
                        RecognitionSettings(RecognitionSettings.NLU.Whisper, whisper_prompt="Greetings of some sort:")
                    )
                    self.assertIn("hello", utterance_1.lower())
                    self.assertEqual('1', av_api.state_get()[World.user.field_name])

                    #Pretending both samples were from speaker 1
                    av_api.recognition_speaker_fix('1')
                    self.check_files('train/0/' + records[0].filename, 'train/1/' + records[1].filename, 'train/1/'+test_0)

                    #Feeging the sample with no voice
                    test_2 = speaker.silence(2)
                    utterance_2 = av_api.recognition_transcribe(test_2, RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model=rhasspy_model))
                    self.assertIsNone(utterance_2)













