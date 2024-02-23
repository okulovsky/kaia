from typing import *
import flask
from pathlib import Path
from kaia.infra import FileIO
from kaia.infra.marshalling_api import MarshallingEndpoint
from .kaia_message import KaiaMessage
import base64
import re


class KaiaEndpoints:
    add_message = MarshallingEndpoint('/change/add_message')
    set_image = MarshallingEndpoint('/change/set_image')


class KaiaApi:
    def __init__(self, address):
        self.caller = MarshallingEndpoint.Caller(address)

    def add_message(self, message: KaiaMessage):
        self.caller.call(KaiaEndpoints.add_message, message)

    def set_image(self, image: bytes):
        self.caller.call(KaiaEndpoints.set_image, image)

    def add_message_fire_and_forget(self, message: KaiaMessage):
        try:
            self.add_message(message)
        except:
            pass



class KaiaWebServer:
    def __init__(self,
                 main_page: Path,
                 static_folder: Path,
                 port: int = 8890,
                 ):
        self._port = port
        self._main_page = FileIO.read_text(main_page)
        self._static_folder = static_folder
        self._chat = []
        self._image: Optional[bytes] = None


    def __call__(self):
        self.app = flask.Flask('Kaia', static_url_path='/static/', static_folder=self._static_folder)
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/updates', view_func=self.updates, methods=['GET'])
        binder = MarshallingEndpoint.Binder(self.app)
        binder.bind_all(KaiaEndpoints, self)
        self.app.run('0.0.0.0', self._port)


    def index(self):
        return self._main_page


    def updates(self):
        update = dict(chat = self._chat)
        if self._image is not None:
            update['image'] = base64.b64encode(self._image).decode('ascii')
        else:
            update['image'] = None
        return flask.jsonify(update)

    def add_message(self, message: KaiaMessage):
        dct = message.__dict__
        dct['text'] = re.sub('\*([^*+])\*', '<i>\1</i>', dct['text'])
        self._chat.append(dct)
        # self._chat = self._chat[-10:]
        return ''

    def set_image(self, image: bytes):
        self._image = image


    @staticmethod
    def debug_kaia_server(
                html: Path,
                static_folder: Path,
                commands_yielder: Callable[[KaiaApi], Generator],
                port: int = 8890,
                cmd_prefix='google-chrome',
                time_between_updates_in_seconds: float = 2,
                stay_after_commands: bool = False
        ):
        from kaia.infra.app import KaiaApp
        import os
        import time
        server = KaiaWebServer(html, static_folder, port)
        app = KaiaApp()
        app.add_subproc_service(server)
        app.run_services_only()

        os.system(f'{cmd_prefix} http://127.0.0.1:{port}/')

        api = KaiaApi(f'127.0.0.1:{port}')
        for _ in commands_yielder(api):
            time.sleep(time_between_updates_in_seconds)

        if stay_after_commands:
            time.sleep(1000)