import pickle
import flask
from foundation_kaia.marshalling import Server
from ...common import Loc
from .service import BrainBoxServiceSettings, BrainBoxService
from ...controllers import ControllerServer, ControllerServerSettings
from flask import Flask
from . import html_helpers
from sqlalchemy.orm import Session
import io

class BrainBoxServer(Server):
    def __init__(self, settings: BrainBoxServiceSettings):
        self.settings = settings
        from .api import BrainBoxApi
        controller_settings = ControllerServerSettings(settings.registry, settings.port, BrainBoxApi(f"127.0.0.1:{settings.port}"))
        self._controller_server = ControllerServer(controller_settings)
        self.service = BrainBoxService(settings)
        super().__init__(settings.port, self.service)

    def __call__(self):
        self.service.run()
        super().__call__()

    def bind_app(self, app: Flask):
        self._controller_server.bind_endpoints(app)
        self._controller_server.bind_custom_endpoints(app)
        self.bind_endpoints(app)
        self.bind_heartbeat(app)
        app.add_url_rule('/', view_func=self._main_page, methods=['GET'])

        app.add_url_rule('/cache/upload/', view_func=self._upload_cache_file, methods=['POST'])
        app.add_url_rule('/cache/download/<fname>', view_func=self._download_cache_file, methods=['GET'])


        app.add_url_rule('/html/jobs/main_page', view_func=self._main_page, methods=['GET'])
        app.add_url_rule('/html/jobs/batch_page/<batch_id>', view_func=self._batch_page, methods=['GET'])
        app.add_url_rule('/html/jobs/operator_log', view_func=self._operator_log, methods=['GET'])

    def _main_page(self):
        with Session(self.service.engine) as session:
            return html_helpers.create_main_page(session)

    def _batch_page(self, batch_id: str):
        with Session(self.service.engine) as session:
            return html_helpers.create_batch_page(session, batch_id)

    def _operator_log(self):
        return html_helpers.create_operator_log_page(self.service.get_operator_log())


    def _upload_cache_file(self):
        for key, value in flask.request.files.items():
            value.save(self.settings.locator.cache_folder/key)
        return 'OK'

    def _download_cache_file(self, fname):
        with open(self.settings.locator.cache_folder/fname, 'rb') as file:
            return flask.send_file(
                io.BytesIO(file.read()),
                mimetype='application/octet-stream'
            )
