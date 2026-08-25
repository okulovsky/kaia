from pathlib import Path
from typing import Any
from .step import LLMRequestStep
from foundation_kaia.prompters import AddressLike, Address

class Image(LLMRequestStep):
    """Attaches an image to the request.

    The value must be a `Path`, which is handed to the task unchanged and therefore
    resolved server-side: images only work against a BrainBox that shares the
    filesystem with the client. Uploading belongs in BrainBoxApi, not here.
    """

    def __init__(self, image_address: AddressLike):
        self.image_address = image_address

    def fill_arguments(self, case: Any, template_entities: dict, arguments: dict):
        image = Address.parse(self.image_address).get(case)
        if not isinstance(image, Path):
            raise ValueError(
                f"Image at `{self.image_address}` must be a Path, but was {type(image)}. "
                f"Images are not uploaded, so only a local BrainBox can read them."
            )
        arguments['image'] = image
