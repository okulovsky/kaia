from abc import ABC, abstractmethod
import threading

lock = threading.Lock()

class ISqlConnection(ABC):
    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self, db):
        pass

    def perform(self, db_function):
        db = None
        cursor = None
        lock.acquire(True)
        try:
            db = self.open()
            cursor = db.cursor()
            result = db_function(cursor)
            db.commit()

            return result
        finally:
            if cursor is not None:
                cursor.close()
            self.close(db)
            lock.release()

