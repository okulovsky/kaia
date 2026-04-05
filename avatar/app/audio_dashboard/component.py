import plotly.io as pio
from fastapi.responses import Response
from starlette.middleware.wsgi import WSGIMiddleware

from foundation_kaia.marshalling_2 import IComponent
from ...messaging import AvatarClient
from .data_reader import DataReader
from .plotter import Plotter
from .dash_app import create_dash_app

_MOUNT_PATH = '/audio_dashboard/dash'


class AudioDashboardComponent(IComponent):
    def __init__(self, client: AvatarClient, past_span_in_seconds: int = 10):
        reader = DataReader(client, past_span_in_seconds)
        self.plotter = Plotter(reader)

    def mount(self, app):
        dash_app = create_dash_app(self.plotter, _MOUNT_PATH + '/')
        app.mount(_MOUNT_PATH, WSGIMiddleware(dash_app.server))

        @app.get('/audio_dashboard/snapshot')
        def snapshot():
            fig = self.plotter.get_figure()
            img_bytes = pio.to_image(fig, format='png')
            return Response(content=img_bytes, media_type='image/png')
