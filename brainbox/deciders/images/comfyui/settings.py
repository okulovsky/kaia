from dataclasses import dataclass, field
from ....framework import ConnectionSettings
from .app.model import ComfyUIModel, ComfyUIInstallation


@dataclass
class ComfyUISettings:
    connection = ConnectionSettings(20301, loading_time_in_seconds=120)
    models_to_install: list[ComfyUIInstallation] = field(default_factory=lambda: [
        ComfyUIInstallation(model=ComfyUIModel(
            'https://civitai.com/api/download/models/46137?type=Model&format=SafeTensor&size=pruned&fp=fp16',
            'checkpoints',
            'meinamix_meinaV9.safetensors',
        )),
        ComfyUIInstallation(model=ComfyUIModel(
            'https://civitai.com/api/download/models/106565?type=Model&format=SafeTensor',
            'loras',
            'cat_lora.safetensors',
        )),
        ComfyUIInstallation(model=ComfyUIModel(
            'https://huggingface.co/Kim2091/AnimeSharp/resolve/main/4x-AnimeSharp.pth',
            'upscale_models',
        )),
        ComfyUIInstallation(component='rgthree-comfy'),
    ])
