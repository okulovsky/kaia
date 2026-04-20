from chara.common import *
from chara.common.tools import Wav
from brainbox.deciders import PiperTraining, Piper
from pathlib import Path
from brainbox import BrainBox


class TrainingCache(ICache):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.training = BrainBoxTrainingCache()
        self.export = BrainBoxCache[PiperTraining.Checkpoint, str]()
        self.delete_training = BrainBoxCache()
        self.upload = BrainBoxCache()
        self.voiceover = BrainBoxCache[str, str]()
        self.delete_voices = BrainBoxCache()




class TrainingPipeline:
    def __init__(self,
                 name: str,
                 base_model: str,
                 parameters: PiperTraining.TrainingParameters,
                 text_to_voiceover: str,
                 ):
        self.name = name
        self.base_model = base_model
        self.parameters = parameters
        self.text_to_voiceover = text_to_voiceover

    def _create_training_task(self, path_to_export_file: Path):
        return PiperTraining.new_task().train(self.name, self.base_model, self.parameters, path_to_export_file)

    def _create_export_task(self, checkpoint):
        return PiperTraining.new_task().export(checkpoint)

    def _create_training_delete_task(self, training_id):
        return PiperTraining.new_task().delete(training_id)

    def _create_upload_task(self, filename):
        return Piper.new_task().upload_tar_voice(filename, filename)

    def _create_voiceover_task(self, filename):
        return Piper.new_task().voiceover(self.text_to_voiceover, filename)

    def _create_delete_task(self, filename):
        return Piper.new_task().delete_voice(filename)


    def __call__(self, cache: TrainingCache,  path_to_export_file: Path):
        @logger.phase(cache.training)
        def _():
            cache.training.pipeline(
                self._create_training_task(path_to_export_file)
            )

        ckpts = [PiperTraining.Checkpoint(**c) for c in cache.training.read_result()]

        @logger.phase(cache.export)
        def _():
            BrainBoxPipeline(self._create_export_task, options_as_files=True).run(cache.export, ckpts)

        file_to_checkpoint = {}
        for checkpoint, file in cache.export.read_cases_and_options():
            file_to_checkpoint[file] = checkpoint

        @logger.phase(cache.delete_training)
        def _():
            BrainBoxPipeline(self._create_training_delete_task).run(cache.delete_training, [self.name])

        files = list(cache.export.read_options())

        @logger.phase(cache.upload)
        def _():
            BrainBoxPipeline(self._create_upload_task).run(cache.upload, files)

        @logger.phase(cache.voiceover)
        def _():
            BrainBoxPipeline(self._create_voiceover_task, options_as_files=True).run(cache.voiceover, files)


        @logger.phase(cache.delete_voices)
        def _():
            BrainBoxPipeline(self._create_delete_task).run(cache.delete_voices, files)

        lst = []
        for filename, file in cache.voiceover.read_cases_and_options():
            v = Wav(cache.voiceover.files.working_folder/file)
            v.assign_metadata(exported_checkpoint=filename, **file_to_checkpoint[filename].__dict__)
            lst.append(v)
        lst = Wav.List(lst)
        cache.write_result(lst)



