from typing import *
import flask
from pathlib import Path

import requests

from kaia.infra import FileIO
from kaia.infra.marshalling_api import MarshallingEndpoint
from .kaia_message import KaiaMessage
import base64
import re
import os

from datetime import datetime
import logging


class KaiaEndpoints:
    add_message = MarshallingEndpoint('/change/add_message')
    set_image = MarshallingEndpoint('/change/set_image')


class KaiaGuiApi(MarshallingEndpoint.API):
    def __init__(self, address):
        super().__init__(address)

    def add_message(self, message: KaiaMessage):
        self.caller.call(KaiaEndpoints.add_message, message)

    def set_image(self, image: bytes):
        self.caller.call(KaiaEndpoints.set_image, image)

    def add_message_fire_and_forget(self, message: KaiaMessage):
        try:
            self.add_message(message)
        except:
            pass

    def updates(self):
        return requests.get(f'http://{self.caller.address}/updates').json()


class StaticPathProvider:
    def __init__(self, folder: Path):
        self.folder = folder

    def get_file(self, path):
        return flask.send_from_directory(self.folder, path)


class KaiaGuiService:
    def __init__(self,
                 main_page: None|Path = None,
                 static_folders: None|Dict[str,Path] = None,
                 port: int = 8890,
                 ):
        self._port = port
        self._main_page = FileIO.read_text(main_page) if main_page is not None else 'Kaia server is running'
        self._static_folders = static_folders
        self._chat = []
        self._image: Optional[bytes] = None
        self._updated_at: Optional[datetime] = None
        self._last_update_requests: Dict[str,datetime] = {}


    def __call__(self):
        self.app = flask.Flask('Kaia', static_folder = None)
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/updates/<session_id>', view_func=self.updates, methods=['GET'])
        self.app.add_url_rule('/updates', view_func=self.updates, methods=['GET'])

        if self._static_folders is not None:
            for url_path, disk_path in self._static_folders.items():
                full_path = f'/{url_path}/<path:path>'
                st = StaticPathProvider(disk_path)
                self.app.add_url_rule(full_path, view_func=st.get_file, endpoint='get_file_'+url_path, methods=['GET'])

        binder = MarshallingEndpoint.Binder(self.app)
        binder.bind_all(KaiaEndpoints, self)

        self.app.run('0.0.0.0', self._port)


    def index(self):
        return self._main_page


    def updates(self, session_id = None):
        if (
            session_id is not None and
            session_id in self._last_update_requests and
            self._updated_at is not None and
            self._updated_at < self._last_update_requests[session_id]
        ):
            self._last_update_requests[session_id] = datetime.now()
            return dict(updated=False)

        if session_id is not None:
            self._last_update_requests[session_id] = datetime.now()

        update = dict(updated=True, chat = self._chat)
        if self._image is not None:
            update['image'] = base64.b64encode(self._image).decode('ascii')
        else:
            update['image'] = None
        return flask.jsonify(update)

    def add_message(self, message: KaiaMessage):
        self._updated_at = datetime.now()
        dct = message.__dict__
        dct['text'] = re.sub('\*([^*+])\*', '<i>\1</i>', dct['text'])
        self._chat.append(dct)

        # self._chat = self._chat[-10:]
        return ''

    def set_image(self, image: bytes):
        self._updated_at = datetime.now()
        self._image = image


    def terminate(self):
        os._exit(0)


    @staticmethod
    def get_default_files_folder():
        return Path(__file__).parent/'web'

    @staticmethod
    def debug_kaia_server(
                html: Path,
                static_folders: Dict[str,Path],
                commands_yielder: Callable[[KaiaGuiApi], Generator],
                port: int = 8890,
                cmd_prefix='google-chrome',
                time_between_updates_in_seconds: float = 2,
                stay_after_commands: bool = False
        ):
        from kaia.infra.app import KaiaApp
        import os
        import time
        server = KaiaGuiService(html, static_folders, port)
        app = KaiaApp()
        app.add_subproc_service(server)
        app.run_services_only()

        os.system(f'{cmd_prefix} http://127.0.0.1:{port}/')

        api = KaiaGuiApi(f'127.0.0.1:{port}')
        for _ in commands_yielder(api):
            time.sleep(time_between_updates_in_seconds)

        if stay_after_commands:
            time.sleep(1000)