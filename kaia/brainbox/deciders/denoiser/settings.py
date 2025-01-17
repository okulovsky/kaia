from dataclasses import dataclass

@dataclass
class DenoiseSettings:
    port: int = 8080
    upload_folder: str = 'uploads'
    output_folder: str = 'outputs'
    allowed_extensions: set = frozenset({'wav'})
