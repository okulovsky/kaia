from dataclasses import dataclass

@dataclass
class WD14TaggerSettings:
    port: int = 11010
    startup_time_in_seconds: int = 5
    models_to_download: tuple[str,...] = (
        'wd14-vit.v2',
    )
