import flask
from foundation_kaia.marshalling import Server
from dataclasses import dataclass
from .components import IAvatarComponent


@dataclass
class AvatarServerSettings:
    components: tuple[IAvatarComponent, ...]
    port: int = 13002


class AvatarServer(Server):
    def __init__(self, settings: AvatarServerSettings):
        self.settings = settings
        super().__init__(self.settings.port)

    def __call__(self):
        app = flask.Flask("AvatarServer", static_folder=None, static_url_path=None)

        import logging
        logging.getLogger('werkzeug').disabled = True

        for component in self.settings.components:
            component.setup_server(app)

        self.bind_heartbeat(app)

        app.run('0.0.0.0', self.settings.port)


