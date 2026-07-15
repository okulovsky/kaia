from dataclasses import dataclass


@dataclass
class OllamaSettings:
    models_to_install: tuple[str, ...] = ('llama3.2:1b',)
