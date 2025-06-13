from unittest import TestCase
from brainbox import BrainBoxApi, BrainBoxTask
from avatar import AvatarApi, AvatarSettings, RecognitionSettings
from avatar.utils import TestSpeaker
from brainbox.deciders import RhasspyKaldi, Collector, OpenTTS, Resemblyzer, Whisper, Vosk
from eaglesong import Utterance
from eaglesong.templates import Template, TemplatesCollection, IntentsPack, TemplateVariable
from eaglesong.templates import OrdinalDub
from yo_fluq import *
from eaglesong.templates import Template, CardinalDub, PluralAgreement


class Templates(TemplatesCollection):
    how_are_you = Template("How are you?")
    cancel_the_timer = Template(f"Cancel the {TemplateVariable('index', OrdinalDub(1,10))} timer")

RESEMBLYZER_MODEL = 'avatar_test'

class RecognitionTestCase(TestCase):

    def make_rhasspy(self, speaker: TestSpeaker, api: AvatarApi):
        rhasspy_model = 'avatar_rec_test'
        intents_pack = IntentsPack(rhasspy_model, tuple(Templates.get_templates()))
        intents_packs = (intents_pack,)
        api.recognition_train(intents_packs)

        # Testing samples
        utterance_0 = api.recognition_transcribe(
            speaker.speak(Templates.how_are_you().to_str()).upload_to_brainbox_with_random_name(),
            RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model=rhasspy_model)
        )
        self.assertIn(utterance_0, Templates.how_are_you)

        utterance_1 = api.recognition_transcribe(
            speaker.speak(Templates.cancel_the_timer(index=2).to_str()).upload_to_brainbox_with_random_name(),
            RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model=rhasspy_model)
        )
        self.assertIn(utterance_1, Templates.cancel_the_timer)
        self.assertEqual(dict(index=2), utterance_1.value)

    def make_whisper(self, speaker: TestSpeaker, api: AvatarApi):
        message = "Hello"
        test_1 = speaker.speak(message, 1).upload_to_brainbox_with_random_name()
        utterance_1 = api.recognition_transcribe(
            test_1,
            RecognitionSettings(RecognitionSettings.NLU.Whisper, whisper_prompt="Greetings of some sort:")
        )
        self.assertIn("hello", utterance_1.lower())

    def make_whisper_with_template(self, speaker: TestSpeaker, api: AvatarApi):
        message = "Five minutes, please"
        test_1 = speaker.speak(message, 1).upload_to_brainbox_with_random_name()
        template = Template(f"{CardinalDub(10).as_variable('minutes')} {PluralAgreement('minutes').as_variable()}, please")
        utterance_1 = api.recognition_transcribe(
            test_1,
            RecognitionSettings(RecognitionSettings.NLU.Whisper, free_speech_recognition_template=template.dub)
        )
        self.assertEqual(dict(minutes=5), utterance_1)

    def make_vosk(self, speaker: TestSpeaker, api: AvatarApi):
        message = 'Hello'
        test_1 = speaker.speak(message, 1).upload_to_brainbox_with_random_name()
        utterance_1 = api.recognition_transcribe(
            test_1,
            RecognitionSettings(RecognitionSettings.NLU.Vosk, vosk_model='en')
        )
        self.assertIn("hello", utterance_1.lower())

    def train_resemblyzer(self, bbapi: BrainBoxApi, api: AvatarApi):
        builder = Collector.TaskBuilder()
        grid = (Query.combinatorics.grid(
            speaker=['p256', 'p257'],
            split=['train'],
            text=["Some text to recognize", "Some more text", "Other text"])
            .to_list()
        )
        for item in grid:
            builder.append(
                BrainBoxTask.call(OpenTTS)(text=item.text, speakerId=item.speaker),
                tags = item
            )
        pack = builder.to_collector_pack('to_media_library')
        path = bbapi.download(bbapi.execute(pack))
        api.recognition_speaker_train(path)


    def make_resemblyzer(self, speaker: TestSpeaker, bbapi: BrainBoxApi, api: AvatarApi):
        test_1 = speaker.speak('Some text to recognize', 'p256').upload_to_brainbox_with_random_name()
        api.recognition_transcribe(
            test_1,
            RecognitionSettings(RecognitionSettings.NLU.Whisper, whisper_prompt="Greetings of some sort:")
        )
        state = api.state_get()
        self.assertEqual('p256', state['user'])

        test_2 = speaker.speak('Some text to recognize', 'p257').upload_to_brainbox_with_random_name()
        api.recognition_transcribe(
            test_2,
            RecognitionSettings(RecognitionSettings.NLU.Whisper, whisper_prompt="Greetings of some sort:")
        )
        state = api.state_get()
        self.assertEqual('p257', state['user'])

        #Now we pretend that both sentences are spoken by p257. So the `test_1` should be moved to the dataset of `p257`
        api.recognition_speaker_fix('p257')

        resources = bbapi.controller_api.list_resources(Resemblyzer, 'datasets/'+RESEMBLYZER_MODEL)
        print(resources)
        d = Query.en(resources).select(lambda z: z.split('/')).group_by(lambda z: z[-2]).to_dictionary(lambda z: z.key, lambda z: [x[-1] for x in z])
        self.assertEqual(3, len(d['p256'])) #Nothing was added
        self.assertEqual(4, len(d['p257']))
        self.assertIn(test_1, d['p257'])


    def test_recognition(self):
        services = [
            RhasspyKaldi(),
            Collector(),
            OpenTTS(),
            Whisper(),
            Resemblyzer(),
            Vosk()
        ]
        with BrainBoxApi.Test(services, always_on_planner=True, stop_containers_at_termination=False) as bb_api:
            speaker = TestSpeaker(bb_api)
            with AvatarApi.Test(AvatarSettings(brain_box_api=bb_api, resemblyzer_model_name=RESEMBLYZER_MODEL)) as av_api:
                with self.subTest('Train resemblyzer'):
                    self.train_resemblyzer(bb_api, av_api)
                with self.subTest('Rhasspy'):
                    self.make_rhasspy(speaker, av_api)
                with self.subTest('Whisper'):
                    self.make_whisper(speaker, av_api)
                with self.subTest('Whisper with free speech template'):
                    self.make_whisper_with_template(speaker, av_api)
                with self.subTest("VOSK"):
                    self.make_vosk(speaker, av_api)
                with self.subTest("Resemblyzer"):
                    self.skipTest('Resemblyzer is not tested at the moment')
                    self.make_resemblyzer(speaker, bb_api, av_api)

