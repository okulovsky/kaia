from .marshalling_metadata import MarshallingMetadata
from .format import Format
import requests

class ApiBinding:
    def __init__(self,
                 address: str,
                 metadata: MarshallingMetadata
                 ):
        self.metadata = metadata
        self.address = address

    def __call__(self, *args, **kwargs):
        address = f'http://{self.address}{self.metadata.get_endpoint_address()}'
        data = self.metadata.signature.to_kwargs_only(*args, **kwargs)


        reply = requests.request(
            self.metadata.endpoint.method,
            address,
            json = Format.encode(data),
        )
        if reply.status_code == 200:
            result = Format.decode(reply.json())
            return result['result']
        try:
            error = reply.json()
        except:
            raise ValueError(f"Call to {address} caused unprocessed error on the server\n\n{reply.text}")
        if 'error' not in error:
            raise ValueError(f"Call to {address} caused unprocessed error on the server\n\n{error}")
        raise ValueError(f"Call to {address} caused exception:\n\n{error['error']}")

