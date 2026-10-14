from foundation_kaia.marshalling import service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class ILlamaLoraServer:
    @brainbox_endpoint
    def completion(self, *, task_name: str, prompt: str|None = None, prompts: list[str]|None = None, max_tokens: int = -1) -> str|list[str]:
        """Generates text completion using a named LoRA adapter task."""
        ...

    @brainbox_endpoint
    def reload(self) -> None:
        """Restarts llama-server inside the container, loading the adapters that are currently in the folder."""
        ...
