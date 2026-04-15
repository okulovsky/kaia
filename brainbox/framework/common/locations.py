import os
from dataclasses import dataclass
from pathlib import Path
from foundation_kaia.misc import Loc


class BrainBoxLocations:
    def __init__(self,
                cache_folder: Path,
                self_test_folder: Path,
                db_path: Path):
        self.cache_folder = cache_folder
        self.self_test_folder = self_test_folder
        self.db_path = db_path

    @staticmethod
    def default(working_folder: Path|None = None) -> 'BrainBoxLocations':
        if working_folder is None:
            working_folder = Loc.data_folder/'brainbox'
        cache = working_folder/'cache'
        self_tests = working_folder/'self_tests'
        os.makedirs(cache, exist_ok=True)
        os.makedirs(self_tests, exist_ok=True)
        return BrainBoxLocations(
            cache,
            self_tests,
            working_folder/'brainbox.db'
        )

    @staticmethod
    def default_resources_folder() -> Path:
        path = Loc.data_folder / 'resources'
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def default_cache_folder() -> Path:
        path = Loc.data_folder/'brainbox/cache'
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def default_self_tests_folder() -> Path:
        path = Loc.data_folder/'self_tests'
        os.makedirs(path, exist_ok=True)
        return path
