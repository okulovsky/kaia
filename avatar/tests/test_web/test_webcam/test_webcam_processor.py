import io
import time
from unittest import TestCase

from PIL import Image

from avatar.daemon import ImageEvent
from avatar.utils import WebTestEnvironmentFactory


class WebcamProcessorTestCase(TestCase):
    def test_threshold_suppresses_upload(self):
        with WebTestEnvironmentFactory(HTML(10)) as env:
            events = []
            for msg in env.client.query(time_limit_in_seconds=30, no_exception=True):
                if isinstance(msg, ImageEvent):
                    events.append(msg)
                if len(events) == 5:
                    break

            self.assertEqual(5, len(events), f'Expected 5 ImageEvents, got {len(events)}')

            percentages = []
            for event in events:
                content = env.api.cache.read(event.file_id)
                img = Image.open(io.BytesIO(content)).convert('RGB')
                pixels = list(img.getdata())
                white = sum(1 for r, g, b in pixels if r == 255 and g == 255 and b == 255)
                pct = round(white / len(pixels) * 100)
                percentages.append(pct)

            self.assertEqual([0, 10, 20, 30, 40], percentages)

def HTML(rate: int):
    return '''<!DOCTYPE html>
    <html><head><meta charset="UTF-8"></head><body>
    <script type="module">
      import { AvatarClient, FakeWebcam, WebcamProcessor } from '/frontend/scripts/kaia-frontend.js';
    
      const client = new AvatarClient({ baseUrl: window.location.origin });
      const webcam = new FakeWebcam({ width: 10, height: 10, whitePercentagePerStep: 0.01 });
      const processor = new WebcamProcessor({
        webcam,
        client,
        baseUrl: window.location.origin,
        rateMs: ''' + str(rate) + ''',
        threshold: 0.09,
      });
      processor.start();
    </script>
    </body></html>
    '''
