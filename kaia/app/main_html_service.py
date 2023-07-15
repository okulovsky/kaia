from typing import *
import os.path
from flask import Flask
from flask_autoindex import AutoIndex
from kaia.infra import Loc
from .app import IKaiaService


class MainHtmlService(IKaiaService):
    def __init__(self,
                 port: int,
                 port_to_name: Dict[int, str],
                 browse_folder: Optional[str] = None
                 ):
        self.port = port
        self.port_to_name = port_to_name
        self.browse_folder = browse_folder

        self.app = Flask(__name__)
        self.file_index = AutoIndex(self.app, browse_root=Loc.data_folder, add_url_rules=False)


        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/data', view_func=self.autoindex, methods=['GET'])
        self.app.add_url_rule('/data/', view_func=self.autoindex, methods=['GET'])
        self.app.add_url_rule('/data/<path:path>', view_func=self.autoindex, methods=['GET'])

    def autoindex(self, path='.'):
        return self.file_index.render_autoindex(path)

    def index(self):
        service_links = '<br>'.join(
            [f'<a href="/" onclick="javascript:event.target.port={port}">{name}</a>' for port, name in
             self.port_to_name.items()])
        if self.autoindex is not None:
            service_links += '<br><a href="/data">Data</a>'
        page = f'''
<html>
<body>
<h1>Kaia main page</h1>
{service_links}
</body>
</html>
'''
        return page

    def run(self, app_config):
        self.app.run('0.0.0.0',self.port)





