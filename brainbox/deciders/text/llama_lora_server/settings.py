from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import LlamaLoraServerModel, LlamaLoraServerLoraAdapter


@dataclass
class LlamaLoraServerSettings:
    connection = ConnectionSettings(20403)
    gguf_models_to_download: tuple[LlamaLoraServerModel, ...] = (
        LlamaLoraServerModel(
            "gemma-3-270m-it",
            "ggml-org/gemma-3-270m-it-GGUF",
            "gemma-3-270m-it-Q8_0.gguf",
        ),
    )
    self_test_lora_adapters: tuple[LlamaLoraServerLoraAdapter, ...] = (
        LlamaLoraServerLoraAdapter(
            "gemma-3-270m-it",
            "yellooot/gemma-3-270m-it-kaia-loras",
            "timer_self_test.gguf",
            "timer_self_test",
        ),
        LlamaLoraServerLoraAdapter(
            "gemma-3-270m-it",
            "yellooot/gemma-3-270m-it-kaia-loras",
            "nutrition_self_test.gguf",
            "nutrition_self_test",
        ),
    )
