import os
import uuid
import zipfile

from selenium.webdriver.common.devtools.v136.cache_storage import delete_entry

from ..dataset.case import DatasetImageCase
from chara import Chara, CaseCollection, brainbox_training_pipeline, BrainBoxCasePipeline, ICase
from pathlib import Path
from brainbox.deciders import OneTrainer
from foundation_kaia.marshalling import JSON
from dataclasses import dataclass
from brainbox import BrainBox

@dataclass
class DownloadedCheckpoint(ICase):
    checkpoint: OneTrainer.Checkpoint
    path: Path|None = None


class LoraTrainer:
    def __init__(self,
                 replace_underscores_with_spaces: bool,
                 parameters: OneTrainer.Parameters,
                 config: str|JSON
                 ):
        self.replace_underscores_with_spaces = replace_underscores_with_spaces
        self.parameters = parameters
        self.config = config

    @property
    def character_identifier(self) -> str:
        return 'CharaLora'+self.parameters.name


    def _export(self,
                cases: CaseCollection[DatasetImageCase],
                ):
        zip_file_path = Chara.current.folder / 'dataset.zip'
        if zip_file_path.exists():
            os.unlink(zip_file_path)

        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for case in cases.successes:
                if case.error is not None or case.tag_annotation.rejected:
                    continue
                zf.write(case.upscaled_local_path, case.source.name)
                txt_name = case.source.name.rsplit('.', 1)[0] + '.txt'
                tags = [tag for tag, accepted in case.tag_annotation.tags.items() if accepted]
                if self.replace_underscores_with_spaces:
                    tags = [t.replace('_', ' ') for t in tags]
                tags = [self.character_identifier] + tags
                zf.writestr(txt_name, ', '.join(tags))

        return str(zip_file_path)

    def _train(self, datset_path: Path):
        @Chara.phase
        def training_id():
            return str(uuid.uuid4())

        id: str = Chara.previous.result
        task = OneTrainer.new_task().train(id, self.parameters, datset_path, self.config)
        result = Chara.call(brainbox_training_pipeline)(task)
        return result

    def _checkpoint_to_task(self, c: DownloadedCheckpoint) -> BrainBox.Task:
        return OneTrainer.new_task().get_checkpoint(c.checkpoint)

    def _download(self, checkpoints: list[OneTrainer.Checkpoint]) -> list[DownloadedCheckpoint]:
        cases = [DownloadedCheckpoint(c) for c in checkpoints]
        unit = BrainBoxCasePipeline(self._checkpoint_to_task, 'path', result_to_file=True)
        result = Chara.call(unit)(CaseCollection(cases)).raise_if_any_error().successes
        for item in result:
            Chara.Apis.brainbox_api.cache.delete(item.path.name)
        return result


    def __call__(self, cases: CaseCollection[DatasetImageCase]):
        dataset_path = Chara.call(self._export)(cases)
        if self.replace_underscores_with_spaces:
            self.parameters.prompts = [p.replace('_', ' ') for p in self.parameters.prompts]
            self.parameters.negatives = self.parameters.negatives.replace('_', ' ')
        self.parameters.prompts = [self.character_identifier+", "+p for p in self.parameters.prompts]
        checkpoints = Chara.call(self._train)(dataset_path)
        checkpoints = [OneTrainer.Checkpoint(**c) for c in checkpoints]
        downloaded_checkpoints = Chara.call(self._download)(checkpoints)
        delete_task = OneTrainer.new_task().delete(downloaded_checkpoints[0].checkpoint.training_id)
        Chara.Apis.brainbox_api.execute(delete_task)
        return downloaded_checkpoints

