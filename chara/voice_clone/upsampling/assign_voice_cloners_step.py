from brainbox.flow import IStep
from copy import copy
from .upsampling_item import UpsamplingItem
from brainbox import BrainBox
from ..voice_cloner import VoiceCloner

class AssignVoiceClonersStep(IStep):
    def __init__(self, cloners: list[VoiceCloner]):
        self.cloners = cloners


    def process(self, history, current: list[UpsamplingItem]):
        result = []
        for obj in current:
            for cloner in self.cloners:
                o = copy(obj)
                o.voice_cloner = cloner
                result.append(o)
        return result

    def get_training_command(self) -> BrainBox.Command:
        return BrainBox.Command(VoiceCloner.joint_training_task(self.cloners))


