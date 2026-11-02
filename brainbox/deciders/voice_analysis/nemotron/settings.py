from dataclasses import dataclass
from enum import Enum
from .app.model import NemotronModelSpec


class NemotronModels(str, Enum):
    multilingual = 'multilingual'


@dataclass
class NemotronSettings:
    models_to_install = {
        NemotronModels.multilingual: NemotronModelSpec(
            # Revision ea30d66 embeds the SentencePiece tokenizer, its weights are those of revision 1c8deae
            url='https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b/resolve/'
                'ea30d66debe3740a08b573244286791d423d6b3e/nemotron-3.5-asr-streaming-0.6b.q8_0.gguf',
            filename='nemotron-3.5-asr-streaming-0.6b.q8_0.gguf',
            size=742090464,
            sha256='3fc991d3badad7277c11030a7519832cddaf2057aafed6d4b25147e953a070b1',
            rnnt_right_context=1,
        ),
    }
