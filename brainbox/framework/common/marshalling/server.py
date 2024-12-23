from .marshalling_metadata import MarshallingMetadata
from flask import Flask
from .server_binding import ServerBinding


class Server:
    def __init__(self, port: int, *objects):
        self.objects = objects
        self.port = port
        metadata = []
        for object in objects:
            metadata.extend(MarshallingMetadata.get_endpoints_from_object(object))
        self.metadata = tuple(metadata)

    def create_alternative_binding(self, name: str, address: str):
        meta = [m for m in self.metadata if m.get_endpoint_address() == address]
        if len(meta) != 1:
            raise ValueError(f"Too much/none ({len(meta)} endpoints for address {address}")
        return ServerBinding(meta[0], name)

    def bind_endpoints(self, app: Flask):
        for metadata in self.metadata:
            app.add_url_rule(
                metadata.get_endpoint_address(),
                view_func=ServerBinding(metadata),
                methods=[metadata.endpoint.method]
            )

    def bind_heartbeat(self, app: Flask):
        app.add_url_rule('/heartbeat', view_func=self.heartbeat, methods=['GET'])

    def bind_app(self, app: Flask):
        self.bind_endpoints(app)
        self.bind_heartbeat(app)


    def heartbeat(self):
        return 'OK'

    def __call__(self):
        app = Flask('RPC_'+'_'.join(type(o).__name__ for o in self.objects))
        self.bind_app(app)
        app.run('0.0.0.0', self.port)