from flask import Flask

from foundation_kaia.marshalling import Server
from .service import AudioControlService
from datetime import datetime
import pandas as pd
import io


class AudioControlServer(Server):
    def __init__(self, service: AudioControlService, port: int):
        self._audio_service = service
        super().__init__(port, service)

    def bind_app(self, app: Flask):
        self.bind_endpoints(app)
        self.bind_heartbeat(app)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        app.add_url_rule('/graph', view_func=self.graph, methods=['GET'])
        app.add_url_rule('/status', view_func=self.status, methods=['GET'])


    def status(self):
        rows = []
        now = datetime.now()
        for m in self._audio_service.cycle.responds_log:
            row = {}
            row['ago'] = (now - m.timestamp).total_seconds()
            if m.exception is not None:
                row['exception'] = m.exception
            if m.iteration_result is not None:
                row['state_b'] = m.iteration_result.mic_state_before.name
                row['state'] = m.iteration_result.mic_state_now.name
                row['play_b'] = None if m.iteration_result.playing_before is None else f'+ {m.iteration_result.playing_before.recording.title}'
                row['play'] = None if m.iteration_result.playing_now is None else f'+ {m.iteration_result.playing_now.recording.title}'
                row['input'] = m.iteration_result.produced_file_name
            rows.append(row)
        return pd.DataFrame(rows).to_html()

    def graph(self):
        from matplotlib import pyplot as plt
        import base64
        df = pd.DataFrame([z.__dict__ for z in self._audio_service.cycle._levels])
        fig, ax = plt.subplots(1,1,figsize=(20,10))
        df.set_index('timestamp').level.plot(ax=ax)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        bts = buf.getvalue()
        base64EncodedStr = base64.b64encode(bts).decode('ascii')
        return f'<img src="data:image/png;base64, {base64EncodedStr}"/>'


    def index(self):
        message_lines = []
        message_lines.append('AudioControlServer is running')
        now = datetime.now()
        message_lines.append(f'Updated {(now-self._audio_service.cycle.last_update_time).total_seconds()} seconds ago')
        df = self.status()
        message_lines.append(df)
        return "<br>".join(message_lines)
        
    def __call__(self):
        self._audio_service.start()
        super().__call__()
        