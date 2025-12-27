from .cache_entity import IFinalizableCacheEntity, TResult, ICacheEntity
from pathlib import Path
from typing import Generic

class EntitiesInitializer:
    def __init__(self, working_folder: Path|None):
        self.working_folder = working_folder
        self._reset()

    def _reset(self):
        self.entities = []
        self.not_ready_found = False

    def set_working_folder(self, working_folder: Path):
        self.working_folder = working_folder
        entities = self.entities
        self._reset()
        for entity in entities:
            self.add(entity[0], entity[1])

    def add(self, name: str, entity: ICacheEntity):
        if self.working_folder is not None:
            entity.initialize(self.working_folder/f'{len(self.entities):02}_{name}')
        if self.not_ready_found:
            entity.delete()
        if self.working_folder is not None:
            if not entity.ready:
                self.not_ready_found = True
        self.entities.append((name, entity))


class ICache(Generic[TResult], IFinalizableCacheEntity[TResult]):
    def __init__(self, working_folder: Path|None = None):
        self._cache_entities_initializer = EntitiesInitializer(working_folder)
        if working_folder is not None:
            self.initialize(working_folder)

    def __setattr__(self, key, value):
        if isinstance(value, ICacheEntity):
            if not hasattr(self, '_cache_entities_initializer'):
                raise ValueError(
                    "You should call ICache.__init__ before adding any CacheEntity fields to the object"
                )
            self._cache_entities_initializer.add(key, value)
        super().__setattr__(key, value)

    def initialize(self, working_folder: Path):
        super().initialize(working_folder)
        self._cache_entities_initializer.set_working_folder(working_folder)

