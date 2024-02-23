from unittest import TestCase
from kaia.brainbox import BrainBoxTestApi, BrainBox, BrainBoxTask, BrainBoxTaskPack, DownloadingPostprocessor
from PIL import Image
import soundfile as sf

class ModelIntegrationTest(TestCase):
    def test_everything(self):
        deciders = BrainBox().create_deciders_dict()
        tasks = self.create_sample_tasks()
        ignore_deciders = ['Oobabooga']
        good_tasks = []
        with BrainBoxTestApi(deciders) as api:
            for decider, task in tasks.items():
                if decider in deciders and not decider in ignore_deciders:
                    api.add(task)
                    good_tasks.append(task)

            for task in good_tasks:
                result = api.join(task)
                print(task.resulting_task.decider, result)






    def check_text(self, s):
        self.assertIsInstance(s, str)


    def create_sample_tasks(self):
        tasks = dict()
        tasks['Automatic1111'] = BrainBoxTaskPack(
            BrainBoxTask(BrainBoxTask.safe_id(), 'Automatic1111', dict(prompt='Cute kitten with a wool ball')),
            postprocessor=DownloadingPostprocessor(0, opener=Image.open)
        )

        tasks['OpenTTS'] = BrainBoxTaskPack(
            BrainBoxTask(BrainBoxTask.safe_id(), 'OpenTTS', dict(voice='coqui-tts:en_vctk', lang='en', speakerId='p225', text="Hello, world!")),
            postprocessor=DownloadingPostprocessor(0, opener = sf.SoundFile)
        )

        tasks['Oobabooga'] = BrainBoxTaskPack(
            BrainBoxTask(BrainBoxTask.safe_id(), 'Oobabooga', dict(prompt="Please provide a recipe for borsch")),
            postprocessor=DownloadingPostprocessor(opener = self.check_text)
        )

        return tasks