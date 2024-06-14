from dataclasses import dataclass
from kaia.infra import Loc

@dataclass
class CoquiTrainingContainerSettings:
    resource_folder = Loc.data_folder/'voice_cloning_training'
    image_name = 'coqui-tts-training'