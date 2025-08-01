from .avatar_component import IAvatarComponent
import flask
from pathlib import Path

class StaticPathsComponent(IAvatarComponent):
    def __init__(self, folders: dict[str, Path]):
        self.folders = folders

    def setup_server(self, app: flask.Flask):
        for url_path, disk_path in self.folders.items():
            StaticPathProvider(url_path, disk_path).add_rule(app)


class StaticPathProvider:
    def __init__(self, url_path: str,  folder: Path):
        self.url_path = url_path
        self.folder = folder

    def get_file(self, path):
        return flask.send_from_directory(self.folder, path)

    def add_rule(self, app: flask.Flask):
        full_path = f'/{self.url_path}/<path:path>'
        app.add_url_rule(full_path, view_func=self.get_file, endpoint='static_get_file_' + self.url_path, methods=['GET'])
