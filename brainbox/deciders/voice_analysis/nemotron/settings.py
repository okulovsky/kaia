from dataclasses import dataclass
from enum import Enum
from .app.model import NemotronModelSpec


class NemotronModels(str, Enum):
    multilingual = 'multilingual'


@dataclass
class NemotronSettings:
    models_to_install = {
        NemotronModels.multilingual: NemotronModelSpec(
            url='https://huggingface.co/nvidia/nemotron-3.5-asr-streaming-0.6b/resolve/'
                '1c8deaecc64b91f034d73e08dd8b64625eb3395d/nemotron-3.5-asr-streaming-0.6b.q8_0.gguf',
            filename='nemotron-3.5-asr-streaming-0.6b.q8_0.gguf',
            size=741548352,
            sha256='a5c435f294eea8f88ce68dd27b8c3bfea7f777cb2fbba04fcd30eaa555f429ae',
            rnnt_right_context=1,
        ),
    }
