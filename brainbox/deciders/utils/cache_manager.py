import os
from ...framework import IDecider, File
import json
from copy import copy

class CacheManager(IDecider):
    def delete(self, files: str|list[str]):
        if isinstance(files,str):
            files = [files]
        for file in files:
            os.unlink(self.cache_folder/file)
