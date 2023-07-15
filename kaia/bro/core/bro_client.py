from typing import *
from ...infra.comm import IStorage, IMessenger
from .space import ISpace, Slot
import time
from abc import ABC, abstractmethod

class IClientDataProvider(ABC):
    @abstractmethod
    def pull(self) -> List[Dict]:
        pass

class StorageClientDataProvider(IClientDataProvider):
    def __init__(self, name, storage: IStorage, data_buffer_length = 1000):
        self.name = name
        self.storage = storage
        self.data_buffer_length = data_buffer_length
        self.last_updated_id = None
        self.data = []

    def pull(self):
        data = self.storage.load_update(self.name, self.data_buffer_length, historical_order=True, last_update_id=self.last_updated_id)
        self.data += [z.value for z in data]
        if self.data_buffer_length is not None:
            if len(self.data) > self.data_buffer_length:
                self.data = self.data[-self.data_buffer_length:]
        if len(data)>0:
            self.last_updated_id = data[-1].id
        return self.data


class DebugClientDataProvider(IClientDataProvider):
    def __init__(self, data = None, delta = 1):
        self.data = data
        self.counter = 0
        self.delta = delta

    def pull(self):
        if self.data is None:
            return []
        self.counter+=self.delta
        if self.counter>=len(self.data):
            self.counter = len(self.data)
        return self.data[:self.counter]





class BroClient:
    def __init__(self,
                 space: ISpace,
                 data_provider: IClientDataProvider,
                 messenger: IMessenger,
                 ):
        self.space = space
        self.data_provider = data_provider
        self.messenger = messenger
        self.last_set_field_set = None



    def disable(self):
        self.messenger.add(None, 'to',self.space.get_name(),'disable')

    def enable(self):
        self.messenger.add(None, 'to',self.space.get_name(),'enable')

    def terminate(self):
        self.messenger.add(None, 'to', 'bro_server', 'terminate')

    def set_field(self, field_name: Union[str, Slot], field_value, validate = True):
        id = self.messenger.add(field_value, 'to', self.space.get_name(), 'set_field', Slot.slotname(field_name))
        self.last_set_field_set = id
        return id

    def check_field_validation(self, id: str):
        while True:
            messages = IMessenger.Query(id=id).query(self.messenger)
            if len(messages) == 0:
                raise ValueError(f'Message with id {id} is not found')
            if messages[0].open:
                time.sleep(0.1)
                continue
            if messages[0].result is None:
                return
            raise ValueError(messages[0].result)

    def check_last_field_validation(self):
        return self.check_field_validation(self.last_set_field_set)

    def get_notifications(self):
        return self.messenger.read_all_and_close(['from', self.space.get_name(), 'notification'])

