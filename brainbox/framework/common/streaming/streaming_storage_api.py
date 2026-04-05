from foundation_kaia.marshalling_2 import ApiCall
from .streaming_storage_interface import IStreamingStorage

class StreamingStorageApi(IStreamingStorage):
    def __init__(self, base_url: str, custom_prefix: str|None = None):
        ApiCall.define_endpoints(self, base_url, IStreamingStorage, custom_prefix)