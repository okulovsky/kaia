import flask
from foundation_kaia.marshalling import Server
from foundation_kaia.web_utils import Component
from dataclasses import dataclass
from .components import IAvatarComponent
import logging
import traceback
from werkzeug.exceptions import HTTPException

def handle_exception(e):
    if isinstance(e, HTTPException):
        return e.get_response()
    tb = traceback.format_exc()
    return flask.Response(tb, status=500, mimetype="text/plain")

@dataclass
class AvatarServerSettings:
    components: tuple[IAvatarComponent|Component, ...]
    port: int = 13002
    hide_logs: bool = True


class AvatarServer(Server):
    def __init__(self, settings: AvatarServerSettings):
        self.settings = settings
        super().__init__(self.settings.port)

    def __call__(self):
        app = flask.Flask("AvatarServer", static_folder=None, static_url_path=None)
        app.register_error_handler(Exception, handle_exception)

        if self.settings.hide_logs:
            logging.getLogger('werkzeug').disabled = True

        av_app = IAvatarComponent.App(app)
        for component in self.settings.components:
            if isinstance(component, IAvatarComponent):
                component.setup_server(av_app, f'127.0.0.1:{self.settings.port}')
            elif isinstance(component, Component):
                component.register(app)


        self.toc = av_app.toc

        self.bind_heartbeat(app)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.run('0.0.0.0', self.settings.port)

    def index(self):
        html = '<html><body>'
        for record in self.toc:
            html+=f'<a href="{record.url}">{record.title}</a><br/>'
        html+="</body></html>"
        return html

