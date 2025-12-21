from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import HFModel, HFLoraAdapter


@dataclass
class LlamaLoraServerSettings:
    connection = ConnectionSettings(20403)
    gguf_models_to_download: tuple[HFModel, ...] = (
        HFModel(
            "gemma-3-270m-it",
            "ggml-org/gemma-3-270m-it-GGUF",
            "gemma-3-270m-it-Q8_0.gguf",
        ),
    )
    self_test_lora_adapters: tuple[HFLoraAdapter, ...] = (
        HFLoraAdapter(
            "gemma-3-270m-it",
            "yellooot/gemma-3-270m-it-kaia-loras",
            "timer_self_test.gguf",
            "timer_self_test",
        ),
        HFLoraAdapter(
            "gemma-3-270m-it",
            "yellooot/gemma-3-270m-it-kaia-loras",
            "nutrition_self_test.gguf",
            "nutrition_self_test",
        ),
    )
