import threading
import weakref
from contextlib import contextmanager
from typing import Any


class ObjectLocks:
    """
    Hands out a threading.RLock per object, keyed by object identity.

    A WeakKeyDictionary is used instead of id(obj): id() is a raw memory
    address, so after an object is garbage collected its id can be reused by
    an unrelated object, which would make the two silently share a lock. The
    weak keys also mean a lock is dropped automatically once its object is
    collected, instead of accumulating forever.
    """
    def __init__(self):
        self._registry_lock = threading.Lock()
        self._locks: "weakref.WeakKeyDictionary[Any, threading.RLock]" = weakref.WeakKeyDictionary()

    def get(self, obj: Any) -> threading.RLock:
        with self._registry_lock:
            result = self._locks.get(obj)
            if result is None:
                result = threading.RLock()
                self._locks[obj] = result
            return result

    @contextmanager
    def lock(self, obj: Any):
        with self.get(obj):
            yield


object_locks = ObjectLocks()
lock = object_locks.lock
