from typing import TypeVar, Generic

TKey = TypeVar('TKey')

class ICacheManager(Generic[TKey]):
    def contains(self, key: TKey) -> bool:
        return False

    def unsafe_get(self, key: TKey):
        raise ValueError(f"Object {key} was not found")

    def get(self, key: TKey):
        if not self.contains(key):
            return None
        return self.unsafe_get(key)

    def store(self, key: TKey, value):
        pass

    def unsafe_delete(self, key: TKey):
        raise ValueError(f"Object {key} was not found")

    def delete(self, key: TKey):
        if self.contains(key):
            self.unsafe_delete(key)





