from unittest import TestCase
from brainbox import BrainBoxApi, BrainBoxTask
from kaia.avatar import AvatarApi, AvatarSettings, RecognitionSettings
from kaia.avatar.utils import TestSpeaker
from brainbox.deciders import RhasspyKaldi, Collector, OpenTTS, Resemblyzer, Whisper
from kaia.dub import Template, TemplatesCollection, IntentsPack
from kaia.dub.languages.en import OrdinalDub
from yo_fluq import *

class Templates(TemplatesCollection):
    how_are_you = Template("How are you?")
    cancel_the_timer = Template("Cancel the {index} timer", index=OrdinalDub(1,10))

RESEMBLYZER_MODEL = 'avatar_test'

class RecognitionTestCase(TestCase):

    def make_rhasspy(self, speaker: TestSpeaker, api: AvatarApi):
        rhasspy_model = 'avatar_rec_test'
        intents_pack = IntentsPack(rhasspy_model, tuple(Templates.get_templates()))
        intents_packs = (intents_pack,)
        api.recognition_train(intents_packs, ())

        # Testing samples
        utterance_0 = api.recognition_transcribe(
            speaker.speak(Templates.how_are_you().to_str()),
            RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model=rhasspy_model)
        )
        self.assertIn(utterance_0, Templates.how_are_you)

        utterance_1 = api.recognition_transcribe(
            speaker.speak(Templates.cancel_the_timer(index=2).to_str()),
            RecognitionSettings(RecognitionSettings.NLU.Rhasspy, rhasspy_model=rhasspy_model)
        )
        self.assertIn(utterance_1, Templates.cancel_the_timer)
        self.assertEqual(dict(index=2), utterance_1.value)

    def make_whisper(self, speaker: TestSpeaker, api: AvatarApi):
        message = "Hello"
        test_1 = speaker.speak(message, 1)
        utterance_1 = api.recognition_transcribe(
            test_1,
            RecognitionSettings(RecognitionSettings.NLU.Whisper, whisper_prompt="Greetings of some sort:")
        )
        self.assertIn("hello", utterance_1.lower())


    def make_resemblyzer(self, speaker: TestSpeaker, bbapi: BrainBoxApi, api: AvatarApi):
        pack = (Query
                .combinatorics.grid(speaker=['p256','p257'], split=['train'], text=["Some text to recognize", "Some more text", "Other text"])
                .feed(Collector.FunctionalTaskBuilder(
                    lambda z: BrainBoxTask.call(OpenTTS)(text=z.text, speakerId=z.speaker)))
        )
        path = bbapi.download(bbapi.execute(pack))
        api.recognition_speaker_train(path)

        test_1 = speaker.speak('Some text to recognize', 'p256')
        api.recognition_transcribe(
            test_1,
            RecognitionSettings(RecognitionSettings.NLU.Whisper, whisper_prompt="Greetings of some sort:")
        )
        state = api.state_get()
        self.assertEqual('p256', state['user'])

        test_2 = speaker.speak('Some text to recognize', 'p257')
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
            Resemblyzer()
        ]
        with BrainBoxApi.Test(services, always_on_planner=True, stop_containers_at_termination=False) as bb_api:
            speaker = TestSpeaker(bb_api)
            with AvatarApi.Test(AvatarSettings(brain_box_api=bb_api, resemblyzer_model_name=RESEMBLYZER_MODEL)) as av_api:
                self.make_rhasspy(speaker, av_api)
                self.make_whisper(speaker, av_api)
                #self.fail("Resemblyzer test is excluded atm")
                self.make_resemblyzer(speaker, bb_api, av_api)
















