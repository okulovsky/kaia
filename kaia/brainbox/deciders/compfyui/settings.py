from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComfyUIFile:
    url: str
    models_subfolder: str|None = None
    filename: str|None = None
    custom_subfolder: str|None = None

    def get_filename(self) -> str:
        if self.filename is not None:
            return self.filename
        return self.url.split('/')[-1]

@dataclass
class ComfyUIExtension:
    git_url: str
    commit: str|None
    has_requirements: bool = False


@dataclass
class ComfyUISettings:
    port: int = 11011
    startup_time_in_seconds: int = 30
    custom_models_folder: Path|None = None

    models_to_download = (
        ComfyUIFile(
            'https://civitai.com/api/download/models/46137?type=Model&format=SafeTensor&size=pruned&fp=fp16',
            'checkpoints',
            'meinamix_meinaV9.safetensors'
        ),
        ComfyUIFile(
            'https://civitai.com/api/download/models/106565?type=Model&format=SafeTensor',
            'loras',
            'cat_lora.safetensors',
        ),
        ComfyUIFile(
            'https://huggingface.co/Kim2091/AnimeSharp/resolve/main/4x-AnimeSharp.pth',
            'upscale_models',
        ),
        ComfyUIFile(
            'https://huggingface.co/SmilingWolf/wd-v1-4-moat-tagger-v2/resolve/main/model.onnx',
            filename='wd-v1-4-moat-tagger-v2.onnx',
            custom_subfolder = 'custom_nodes/ComfyUI-WD14-Tagger/models',
        ),
        ComfyUIFile(
            'https://huggingface.co/SmilingWolf/wd-v1-4-moat-tagger-v2/resolve/main/selected_tags.csv',
            filename='wd-v1-4-moat-tagger-v2.csv',
            custom_subfolder = 'custom_nodes/ComfyUI-WD14-Tagger/models',
        ),
    )

    extensions: tuple[ComfyUIExtension,...] = (
        ComfyUIExtension(
            'https://github.com/pythongosssss/ComfyUI-WD14-Tagger',
            'd33501765c5bf3dca6e90e0ebaa962890999fbc5',
            True
        ),
        ComfyUIExtension(
            'https://github.com/pythongosssss/ComfyUI-Custom-Scripts',
            'ae052b625fb4c0b2dfc1649ae4c2b789f4b2bece'
        )
    )

    extension_requirements: tuple[str,...] = (
        'onnxruntime==1.19.2',
    )

