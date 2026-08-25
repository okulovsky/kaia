import base64
from unittest import TestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from avatar.daemon import VideoCommand
from avatar.utils.web_test_environment import WebTestEnvironmentFactory


class VideoHandlerTestCase(TestCase):
    def test_video_handler(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.api.cache.upload('v1.webm', base64.b64decode(V1_B64))
            env.api.cache.upload('v2.webm', base64.b64decode(V2_B64))
            env.api.cache.upload('final.png', _PNG)

            env.driver.find_element(By.ID, "processBtn").click()

            visible_layers = lambda d: len([
                v for v in d.find_elements(By.CSS_SELECTOR, '#stage video')
                if v.value_of_css_property('opacity') != '0'
            ])
            WebDriverWait(env.driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, '#stage video')) == 2
            )
            self.assertEqual(0, visible_layers(env.driver))

            env.client.push(VideoCommand(['v1.webm', 'v2.webm'], 'final.png'))

            WebDriverWait(env.driver, 30).until(
                lambda d: (d.find_element(By.ID, "preview").get_attribute("src") or '')
                          .endswith('/cache/open/final.png')
            )

            events = env.driver.execute_script("return window.__events")
            fetched = [e[1] for e in events if e[0] == 'fetch']
            self.assertEqual(['v1.webm', 'v2.webm'], fetched)

            played = [e[1] for e in events if e[0] == 'play']
            self.assertEqual([3, 9], played)

            # the second video is downloaded while the first one is still playing
            self.assertLess(
                events.index(['fetch', 'v2.webm']),
                events.index(['ended', 1]),
            )

            # the memory of both videos is released
            self.assertEqual(2, env.driver.execute_script("return window.__revoked"))

            # exactly one layer covers the image while a video plays, none afterwards
            self.assertEqual([1, 1], [e[1] for e in events if e[0] == 'visible'])
            WebDriverWait(env.driver, 10).until(lambda d: visible_layers(d) == 0)


V1_B64 = (
    'GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJChYECGFOAZwEAAAAAAAJOEU2bdLpNu4tTq4QVSalmU6yBoU27i1OrhBZU'
    'rmtTrIHYTbuMU6uEElTDZ1OsggEiTbuMU6uEHFO7a1OsggI47AEAAAAAAABZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmsirXsYMPQkBNgI1M'
    'YXZmNTguNzYuMTAwV0GNTGF2ZjU4Ljc2LjEwMESJiEBywAAAAAAAFlSua8WuAQAAAAAAADzXgQFzxYgBCAt6bJhytJyBACK1nIN1'
    'bmSGhVZfVlA4g4EBI+ODhAX14QDgAQAAAAAAAAmwgSC6gSCagQISVMNnQJpzcwEAAAAAAAAnY8CAZ8gBAAAAAAAAGkWjh0VOQ09E'
    'RVJEh41MYXZmNTguNzYuMTAwc3MBAAAAAAAAX2PAi2PFiAEIC3psmHK0Z8gBAAAAAAAAIkWjh0VOQ09ERVJEh5VMYXZjNTguMTM0'
    'LjEwMCBsaWJ2cHhnyKJFo4hEVVJBVElPTkSHlDAwOjAwOjAwLjMwMDAwMDAwMAAAH0O2dfHngQCjvoEAAIAQAwCdASogACAAAEcI'
    'hYWIhYSIAgICdaoD+AP6AghZDL0A/v1u8//jmTcwxP+Obf/xYTwOKMj/8VEAo5WBAGQAsQEAARAQABgAGFgv9AAIcACjlYEAyACx'
    'AQABEBAAGAAYWC/0AAhwABxTu2uRu4+zgQC3iveBAfGCAcLwgQM='
)

V2_B64 = (
    'GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQJChYECGFOAZwEAAAAAAALYEU2bdLpNu4tTq4QVSalmU6yBoU27i1OrhBZU'
    'rmtTrIHYTbuMU6uEElTDZ1OsggEiTbuMU6uEHFO7a1OsggLC7AEAAAAAAABZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmsirXsYMPQkBNgI1M'
    'YXZmNTguNzYuMTAwV0GNTGF2ZjU4Ljc2LjEwMESJiECMIAAAAAAAFlSua8WuAQAAAAAAADzXgQFzxYjh7Itbu/Icr5yBACK1nIN1'
    'bmSGhVZfVlA4g4EBI+ODhAX14QDgAQAAAAAAAAmwgSC6gSCagQISVMNnQJpzcwEAAAAAAAAnY8CAZ8gBAAAAAAAAGkWjh0VOQ09E'
    'RVJEh41MYXZmNTguNzYuMTAwc3MBAAAAAAAAX2PAi2PFiOHsi1u78hyvZ8gBAAAAAAAAIkWjh0VOQ09ERVJEh5VMYXZjNTguMTM0'
    'LjEwMCBsaWJ2cHhnyKJFo4hEVVJBVElPTkSHlDAwOjAwOjAwLjkwMDAwMDAwMAAAH0O2dUD654EAo72BAACA0AIAnQEqIAAgAABH'
    'CIWFiIWEiAICAnWqA/gCCCEIPQD+/00S//xYV/FhX8WFf/FhX/z8zu3F/OYAo5WBAGQAsQEAARAQABgAGFgv9AAIcACjlYEAyACx'
    'AQABEBAAGAAYWC/0AAhwAKOVgQEsALEBAAEQEAAYABhYL/QACHAAo5WBAZAAsQEAARAQABgAGFgv9AAIcACjlYEB9ACxAQABEBAA'
    'GAAYWC/0AAhwAKOVgQJYALEBAAEQEAAYABhYL/QACHAAo5WBArwAsQEAARAQFGAAYWC/0AAhwACjlYEDIACxAQABEBAAGAAYWC/0'
    'AAhwABxTu2uRu4+zgQC3iveBAfGCAcLwgQM='
)

_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    b'\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82'
)


HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>VideoCommand Test</title></head>
<body>
  <button id="processBtn">Start</button>
  <div id="stage" style="position: relative; width: 320px; height: 240px;">
    <img id="preview" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%;" />
  </div>
  <script type="module">
    import { AvatarClient, Dispatcher, ImageCommandHandler, VideoCommandHandler } from '/frontend/scripts/kaia-frontend.js';

    window.__events = [];
    window.__revoked = 0;
    let endedCount = 0;

    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, init) => {
      const url = typeof input === 'string' ? input : input.url;
      const match = /\\/cache\\/open\\/([^?]+)/.exec(url);
      if (match) window.__events.push(['fetch', decodeURIComponent(match[1])]);
      return originalFetch(input, init);
    };

    const originalRevoke = URL.revokeObjectURL.bind(URL);
    URL.revokeObjectURL = (url) => { window.__revoked += 1; return originalRevoke(url); };

    const btn   = document.getElementById('processBtn');
    const imgEl = document.getElementById('preview');
    const stage = document.getElementById('stage');

    const visible = () => Array.from(stage.querySelectorAll('video'))
                               .filter(v => getComputedStyle(v).opacity !== '0');

    // media events do not bubble, but they do reach the container in the capture phase
    stage.addEventListener('play', (e) => {
      window.__events.push(['play', Math.round(e.target.duration * 10)]);
      window.__events.push(['visible', visible().length]);
    }, true);
    stage.addEventListener('ended', () => {
      endedCount += 1;
      window.__events.push(['ended', endedCount]);
    }, true);

    btn.addEventListener('click', () => {
      const client       = new AvatarClient({baseUrl: window.location.origin});
      const dispatcher   = new Dispatcher(client);
      const imageHandler = new ImageCommandHandler({ dispatcher, imgEl });
      new VideoCommandHandler({ dispatcher, container: stage, imageHandler, baseUrl: window.location.origin });
      dispatcher.start();
    });
  </script>
</body>
</html>
'''
