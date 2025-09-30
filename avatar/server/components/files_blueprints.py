from foundation_kaia.web_utils.file_cache import FileCacheComponent
from pathlib import Path

class ResourcesComponent(FileCacheComponent):
    def __init__(self, resources_folder: Path):
        super().__init__(resources_folder, '/resources')

