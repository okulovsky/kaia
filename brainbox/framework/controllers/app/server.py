import os
import pickle
import traceback
import flask
from ...common.marshalling import Server
from .service import ControllerServerSettings, ControllerService
from flask import Flask
from . import html_helpers
from ...common import Loc
import io
from ..controller import create_self_test_report_page

class ControllerServer(Server):
    def __init__(self, settings: ControllerServerSettings):
        self.settings = settings
        self.service = ControllerService(settings)
        super().__init__(
            settings.port,
            self.service
        )

    def bind_custom_endpoints(self, app):
        app.add_url_rule(
            '/html/controllers/status',
            view_func=self._html_status,
            methods=['GET']
        )

        app.add_url_rule(
            '/html/controllers/installation_report',
            view_func=self._controllers_installation_report,
            methods=['GET']
        )

        app.add_url_rule(
            '/html/controllers/self_test_report/<decider>',
            view_func=self._controllers_self_test_report,
            methods=['GET']
        )

        app.add_url_rule(
            '/resources/upload/<decider_name>/<path:path>',
            view_func=self._resources_upload,
            methods=['POST']
        )

        app.add_url_rule(
            '/resources/download/<decider_name>/<path:path>',
            view_func=self._resources_download,
            methods=['GET']
        )


    def bind_app(self, app: Flask):
        super().bind_app(app)
        self.bind_custom_endpoints(app)
        app.add_url_rule('/', view_func=self._html_status, methods=['GET'])



    def _html_status(self):
        return html_helpers.create_status_page(self.service.status())

    def _controllers_installation_report(self):
        return html_helpers.create_installation_report_page(self.service.installation_report())


    def _controllers_self_test_report(self, decider: str):
        with open(self.settings.registry.locator.self_test_path/decider, 'rb') as file:
            report = pickle.load(file)
        return create_self_test_report_page(report)


    def _resources_upload(self, decider_name: str, path: str):
        try:
            self.service.get_controller(decider_name)
            path = self.settings.registry.locator.resources_folder/decider_name/path
            count = 0
            for key, value in flask.request.files.items():
                if count>0:
                    raise ValueError("Only one file is expected")
                os.makedirs(path.parent, exist_ok=True)
                value.save(path)
                count += 1
            return 'OK'
        except:
            return traceback.format_exc(), 500


    def _resources_download(self, decider_name: str, path: str):
        try:
            self.service.get_controller(decider_name)
            path = self.settings.registry.locator.resources_folder / decider_name / path
            with open(path, 'rb') as file:
                return flask.send_file(
                    io.BytesIO(file.read()),
                    mimetype='application/octet-stream'
                )
        except:
            return traceback.format_exc(), 500
