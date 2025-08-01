from ..daemon import PhonixDeamon, RecordingApi
from .monitoring import create_dash_app, PhonixMonitoring
from .file_list import UploadedFileController
from threading import Thread
import flask

class PhonixServer:
    def __init__(self, daemon: PhonixDeamon, recording_api: RecordingApi, port=13001):
        self.port = port
        self.daemon = daemon
        self.client = self.daemon.client.clone()
        self.file_controller = UploadedFileController(self.daemon.client.clone(), recording_api)


    def update_data(self, data):
        data.extend(self.client.pull())

    def __call__(self):
        thread = Thread(target=self.daemon.run, daemon=True)
        thread.start()

        app = flask.Flask(__name__)
        app.add_url_rule('/', view_func=self.file_controller.get_list_html, methods=['GET'])
        app.add_url_rule('/play/<filename>', view_func=self.file_controller.serve_file, methods=['GET'])
        dash_app = create_dash_app(PhonixMonitoring(self.update_data))
        dash_app.init_app(app)

        app.run('0.0.0.0', self.port)




