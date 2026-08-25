import os
from pathlib import Path

class CreativeArticulatorLocations:
    def __init__(self,
                 working_folder: Path,
                 structure_file: Path|None = None
                 ):
        self.working_folder = working_folder
        self.custom_structure_file = structure_file

        os.makedirs(self.caches, exist_ok=True)

    @property
    def caches(self):
        return self.working_folder/'caches'

    @property
    def folder_caches(self):
        return self.caches/'folders'

    @property
    def file_caches(self):
        return self.caches/'files'

    @property
    def section_caches(self):
        return self.caches/'sections'

    @property
    def block_caches(self):
        return self.caches/'blocks'

    @property
    def structure(self):
        if self.custom_structure_file is None:
            return self.working_folder/'structure.txt'
        return self.custom_structure_file
