from dataclasses import dataclass


class ParlerTtsModels:
    MiniV1 = 'mini-v1'
    LargeV1 = 'large-v1'
    MiniMultilingualV11 = 'mini-multilingual-v1.1'

    REPOSITORIES = {
        MiniV1: 'parler-tts/parler-tts-mini-v1',
        LargeV1: 'parler-tts/parler-tts-large-v1',
        MiniMultilingualV11: 'parler-tts/parler-tts-mini-multilingual-v1.1',
    }


@dataclass
class ParlerTtsSettings:
    models_to_install = {
        ParlerTtsModels.MiniV1: ParlerTtsModels.REPOSITORIES[ParlerTtsModels.MiniV1],
    }
