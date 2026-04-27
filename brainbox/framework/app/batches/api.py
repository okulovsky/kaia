from foundation_kaia.marshalling import ApiCall
from .interface import IBatchesService


class BatchesApi(IBatchesService):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, IBatchesService)
