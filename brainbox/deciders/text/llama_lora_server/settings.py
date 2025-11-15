from dataclasses import dataclass
from ....framework import ConnectionSettings
from pathlib import Path
from .model import HFModel


@dataclass
class LlamaLoraServerSettings:
    connection = ConnectionSettings(20403)
    gguf_model = HFModel("unsloth/gemma-3-270m-it-GGUF", "models", "gemma-3-270m-it-Q8_0.gguf")
    self_test_lora_adapters = [
        HFModel("yellooot/gemma-3-270m-it-kaia-loras", "lora_adapters", "timer_self_test.gguf"),
        HFModel("yellooot/gemma-3-270m-it-kaia-loras", "lora_adapters", "nutrition_self_test.gguf"),
    ]
