import copy
from dataclasses import dataclass
from brainbox.deciders.images.comfyui.workflows import IWorkflow
from chara.common import Character
from .settings import KreaSettings
from ...common import Theme, Clothing, Scene, Shot, assemble_tags
from ...common import IImageScenario
from ..workflow import KreaImageToImage
import random

@dataclass
class KreaCase(IImageScenario):
    character: Character
    settings: KreaSettings
    theme: Theme
    activity: str|None = None
    scene: Scene|None = None
    clothing: Clothing|None = None
    shot: Shot|None = None
    face: str|None = None

    def get_other_tags(self) -> str|None:
        return None

    def to_prompt(self) -> str:
        activity_desc = self.settings.activity_template.format(self.activity)
        prompt = assemble_tags(
            activity_desc,
            self.scene.to_prompt() if self.scene else None,
            self.clothing.to_prompt() if self.clothing else None,
            self.face,
            self.shot.to_prompt() if self.shot else None,
            self.get_other_tags(),
            self.settings.prompt_suffix
        )
        return prompt


    def to_workflow(self) -> IWorkflow:
        workflow = copy.deepcopy(self.settings.workflow_template)
        workflow.source_image = self.settings.name_to_source_filename_template.format(self.character.name)
        workflow.prompt = self.to_prompt()
        workflow.seed = random.randint(0, 100000000)
        return workflow
