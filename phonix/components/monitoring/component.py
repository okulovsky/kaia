from .monitoring import create_dash_app, PhonixMonitoring
from avatar.server import IAvatarComponent, AvatarStream, AvatarApi
from avatar.daemon import SoundEvent, SoundConfirmation
from avatar.messaging import StreamClient
from datetime import datetime
from io import BytesIO
import flask
from yo_fluq import FileIO
from pathlib import Path
import time
from ...daemon import (
    SoundLevelReport, SilenceLevelReport,
    MicStateChangeReport, SoundPlayStarted
)



REQUIRED_TYPES = (
    SoundLevelReport,
    SilenceLevelReport,
    MicStateChangeReport,
    SoundPlayStarted,
    SoundConfirmation
)

class PhonixMonitoringComponent(IAvatarComponent):
    def __init__(self, folder: Path):
        self.folder = folder
        self.client: StreamClient|None = None
        self.address: str|None = None
        self.monitoring: PhonixMonitoring|None = None
        self.files = []
        self.last_update: float|None = None

    def init_monitor(self):
        self.client = AvatarStream(AvatarApi(self.address)).create_client()
        self.client = self.client.with_types(*REQUIRED_TYPES)
        self.client.initialize()
        return "OK"

    def update_data(self, data):
        if self.client is None:
            self.init_monitor()
        now = time.monotonic()
        if self.last_update is None or now - self.last_update > 20:
            data.clear()
            self.files.clear()
            messages = self.client.pull_tail(100)
        else:
            messages = self.client.pull()
        self.last_update = now
        data.extend(messages)
        for m in messages:
            if isinstance(m, SoundEvent):
                self.files.append(m.file_id)
        if len(self.files)>10:
            self.files = self.files[-10:]


    def setup_server(self, app: IAvatarComponent.App, address: str):
        self.monitoring = PhonixMonitoring(self.update_data)
        dash_app = create_dash_app(self.monitoring, '/phonix-monitor/graph/')
        dash_app.init_app(app.app)
        app.add_url_rule('/phonix-monitor/', view_func=self.monitor, methods=['GET'], caption="Monitoring microphone state, low-level events and files")
        app.add_url_rule('/phonix-monitor/init', view_func=self.init_monitor, methods=['POST'])
        app.add_url_rule('/phonix-monitor/screenshot', self.screenshot, ['GET'])
        app.add_url_rule('/phonix-monitor/files', self.get_files, methods=['GET'])
        app.add_url_rule('/phonix-monitor/files/list', self.files_list, methods=['GET'])
        app.add_url_rule('/phonix-monitor/files/audio/<file_id>', self.audio, methods=['GET'])

        self.address = address

    def monitor(self):
        return MAIN_HTML

    def get_files(self):
        return FILES_HTML

    def files_list(self):
        return flask.jsonify(list(reversed(self.files)))

    def audio(self, file_id):
        wav_bytes = FileIO.read_bytes(self.folder/file_id)
        return flask.Response(
            wav_bytes,
            mimetype='audio/wav',
            headers={
                'Content-Disposition': f'inline; filename="{file_id}"'
            }
        )

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



MAIN_HTML = '''
<!doctype html>
<html>
<meta charset="utf-8">
<title>Phonix monitor</title>
<style>
  html, body {
    height: 100%;
    margin: 0;
  }
  iframe {
    width: 100%;
    border: none;
    overflow: hidden;
  }
</style>
<body>
  <iframe src="/phonix-monitor/graph" style="height:70%"></iframe>
  <iframe src="/phonix-monitor/files" style="height:30%"></iframe>
</body>
</html>
'''


FILES_HTML = '''<!doctype html>
<html>
<meta charset="utf-8">
<title>Audio List</title>

<div id="tracks"></div>

<script>
  const LIST_URL = '/phonix-monitor/files/list';
  const FILE_URL = '/phonix-monitor/files/audio';

  let prevSignature = '';

  async function poll() {
    try {
      const res = await fetch(LIST_URL, {cache: 'no-store'});
      if (!res.ok) return;
      const data = await res.json();
      const items = Array.isArray(data) ? data : [];
      const signature = JSON.stringify(items);
      if (signature !== prevSignature) {
        render(items);
        prevSignature = signature;
      }
    } catch {}
  }

  function render(names) {
    const container = document.getElementById('tracks');
    container.innerHTML = '';
    for (const name of names) {
      const audio = document.createElement('audio');
      audio.controls = true;
      audio.src = FILE_URL + '/' + name;
      audio.preload = 'none';
      container.appendChild(audio);
    }
  }

  setInterval(poll, 1000);
</script>
</html>
'''