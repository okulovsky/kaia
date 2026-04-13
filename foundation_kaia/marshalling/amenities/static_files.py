from pathlib import Path
from fastapi.staticfiles import StaticFiles
from ..protocol import IComponent


class StaticFilesComponent(IComponent):
    def __init__(self, directory: Path, path: str = '/static'):
        self.directory = directory
        self.path = path

    def mount(self, app):
        app.mount(self.path, StaticFiles(directory=self.directory, html=True), name='static')
