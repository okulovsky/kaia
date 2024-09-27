from kaia.infra.marshalling_api import MarshallingEndpoint
from queue import Queue
import requests
import struct
from threading import Thread
from dataclasses import dataclass

@dataclass
class _Request:
    send: bool
    cancel: bool


class RequestedException(Exception):
    pass



class WavStreamingRequest:
    def __init__(self, address: None|str, file_name: str, sample_rate: int, frame_length, initial_buffer: list[list[int]]):
        if address is not None:
            MarshallingEndpoint.check_address(address)
        self.address = address
        self.file_name = file_name
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.queue = Queue()
        self.thread = Thread(target = self._make_request, daemon=True)
        self.thread.start()
        for data in initial_buffer:
            self.add_wav_data(data)


    def _generator(self):
        while True:
            buffer = self.queue.get(True)
            if isinstance(buffer, _Request):
                if buffer.send:
                    break
                if buffer.cancel:
                    raise RequestedException()
            yield buffer

    def _make_request(self):
        try:
            if self.address is not None:
                requests.post(
                    f'http://{self.address}/upload/{self.sample_rate}/{self.frame_length}/{self.file_name}',
                    data=self._generator()
                )
            else:
                for _ in self._generator():
                    pass
        except RequestedException:
            pass


    def add_wav_data(self, data):
        to_send = struct.pack("h"*len(data), *data)
        self.queue.put(to_send)

    def send(self):
        self.queue.put(_Request(True, False))
        self.thread.join()

    def cancel(self):
        self.queue.put(_Request(False, True))
        self.thread.join()







