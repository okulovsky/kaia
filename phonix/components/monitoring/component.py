from .monitoring import create_dash_app, PhonixMonitoring
from avatar.server import IAvatarComponent, AvatarStream, AvatarApi
from datetime import datetime
from io import BytesIO
import flask
from yo_fluq import FileIO

class PhonixMonitoringComponent(IAvatarComponent):
    def __init__(self):
        self.client = None
        self.monitoring: PhonixMonitoring|None = None
    def update_data(self, data):
        data.extend(self.client.pull())

    def screenshot(self):
        self.monitoring.data.extend(self.client.pull())
        figure = self.monitoring.create_figure(self.monitoring.data, datetime.now())
        io = BytesIO()

        figure.write_image(io, width=1000, height=600)

        return flask.Response(
            io.getvalue(),
            mimetype='image/png',
            headers={
                'Content-Disposition': 'inline; filename="screenshot.png"',
                'Content-Length': str(len(io.getvalue()))
            }
        )



    def setup_server(self, app: IAvatarComponent.App, address: str):
        self.client = AvatarStream(AvatarApi(address)).create_client()
        self.monitoring = PhonixMonitoring(self.update_data)
        dash_app = create_dash_app(self.monitoring)
        dash_app.init_app(app.app)
        app.add_link('/phonix-monitor',"Monitoring microphone state and low-level events")
        app.add_url_rule('/phonix-monitor/screenshot', self.screenshot, ['GET'])




