from dataclasses import dataclass
from enum import Enum

class CosyVoiceModels(str, Enum):
    FunCosyVoice = 'Fun-CosyVoice3-0.5B-2512'
    CosyVoice2 = 'CosyVoice2-0.5B'
    CosyVoice = 'CosyVoice-300M'
    CosyVoiceSFT = 'CosyVoice-300M-SFT'
    CosyVoiceInstruct = 'CosyVoice-300M-Instruct'
    CosyVoiceTTSFRD = 'CosyVoice-ttsfrd'


@dataclass
class CosyVoiceSettings:
    models_to_install = [
        CosyVoiceModels.FunCosyVoice,
        CosyVoiceModels.CosyVoice2,
        CosyVoiceModels.CosyVoice,
        CosyVoiceModels.CosyVoiceSFT,
        CosyVoiceModels.CosyVoiceInstruct,
        CosyVoiceModels.CosyVoiceTTSFRD
    ]
