from dataclasses import dataclass, field

@dataclass
class ImageScenarioSettings:
    activities_per_case: int = 20
    tags_collection: str = 'CharaImageTags'
    tags_per_activity: int = 30
    tags_per_scene_attribute: int = 3
    llm: str = 'mistral-small'

