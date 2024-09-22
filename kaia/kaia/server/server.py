import json
from typing import *
import flask
from pathlib import Path
import base64
import re
import os
from datetime import datetime
from kaia.infra import Loc, FileIO
from bus import Bus, BusItem
from dataclasses import dataclass, field



class StaticPathProvider:
    def __init__(self, folder: Path):
        self.folder = folder

    def get_file(self, path):
        return flask.send_from_directory(self.folder, path)

@dataclass
class KaiaServerSettings:
    db_path: Path
    file_cache_folder: Path
    main_static_folder: Path = Loc.root_folder/'web/static'
    additional_static_folders: dict[str, Path] | None = None
    port: int = 8890
    web_folder: Path = Loc.root_folder/'web'


class KaiaServer:
    def __init__(self, settings: KaiaServerSettings):
        self.settings = settings

    def __call__(self):
        self._bus = Bus(self.settings.db_path)

        self.app = flask.Flask('Kaia', static_folder = None)
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/command/<session_id>/<command_type>', view_func=self.command, methods=['POST'])
        self.app.add_url_rule('/updates/<session_id>/<last_update_id>', view_func=self.updates, methods=['GET'])
        self.app.add_url_rule('/file/<file_id>', view_func=self.file, methods=['GET'])
        self.app.add_url_rule('/heartbit', view_func=self.heartbit, methods=['GET'])

        static_folders = dict(static = self.settings.main_static_folder)
        if self.settings.additional_static_folders is not None:
            for k, v in self.settings.additional_static_folders.items():
                static_folders[k] = v
        for url_path, disk_path in static_folders.items():
            full_path = f'/{url_path}/<path:path>'
            st = StaticPathProvider(disk_path)
            self.app.add_url_rule(full_path, view_func=st.get_file, endpoint='get_file_'+url_path, methods=['GET'])

        self.app.run('0.0.0.0', self.settings.port)


    def index(self):
        return FileIO.read_text(self.settings.web_folder/'index.html')

    def heartbit(self):
        return 'OK'

    def command(self, session_id: str, command_type: str):
        self._bus.add_message(BusItem(
            session_id = session_id,
            timestamp = datetime.now(),
            type = command_type,
            payload = json.dumps(flask.request.json)
        ))
        return "OK"

    def updates(self, session_id: str, last_update_id: str):
        last_update_id = int(last_update_id)
        items = self._bus.get_messages(session_id, last_update_id)
        result = []
        for item in items:
            result.append(dict(
                id = item.id,
                timestamp = str(item.timestamp),
                type = item.type,
                payload = json.loads(item.payload)
            ))
        return flask.jsonify(result)

    def file(self, file_id: str):
        return flask.send_file(self.settings.file_cache_folder/file_id)



