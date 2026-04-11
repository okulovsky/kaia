import base64
import plotly.io as pio
from fastapi.responses import Response, HTMLResponse
from starlette.middleware.wsgi import WSGIMiddleware

from foundation_kaia.marshalling_2 import IComponent
from ...messaging import AvatarClient
from .data_reader import DataReader
from .plotter import Plotter
from .dash_app import create_dash_app
from pathlib import Path

_MOUNT_PATH = '/audio_dashboard/dash'


class AudioDashboardComponent(IComponent):
    def __init__(self, client: AvatarClient, cache_folder: Path, past_span_in_seconds: int = 10):
        self.cache_folder = cache_folder
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

        @app.get('/audio_dashboard/preview/{file_id}')
        def preview(file_id: str):
            data = (self.cache_folder/file_id).read_bytes()
            b64 = base64.b64encode(data).decode()
            html = f"""<!DOCTYPE html>
<html>
<body>
<audio controls autoplay>
  <source src="data:audio/wav;base64,{b64}" type="audio/wav">
</audio>
</body>
</html>"""
            return HTMLResponse(content=html)


