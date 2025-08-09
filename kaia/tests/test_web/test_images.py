from kaia.tests.test_web.environment import TestEnvironmentFactory
from unittest import TestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from avatar.services import ImageCommand
import base64

class ImageHandlerTestCase(TestCase):
    def test_image_handler(self):
        with TestEnvironmentFactory(HTML) as env:
            png_bytes = b'\x89PNG\r\n\x1a\n'
            b64 = base64.b64encode(png_bytes).decode('ascii')
            env.client.put(ImageCommand(base_64=b64))

            driver = env.driver

            process_btn = driver.find_element(By.ID, "processBtn")
            process_btn.click()

            # 3) wait until the <img> src updates to our data URL
            expected_src = f'data:image/png;base64,{b64}'
            WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.ID, "preview").get_attribute("src") == expected_src
            )

            # 4) final assertion
            actual = driver.find_element(By.ID, "preview").get_attribute("src")
            self.assertEqual(actual, expected_src)


HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ImageCommand Test</title></head>
<body>
  <button id="processBtn">Start</button>
  <img id="preview" />
  <script type="module">
    import { AvatarClient } from '/scripts/client.js';
    import { Dispatcher }     from '/scripts/dispatcher.js';
    import { ImageCommandHandler } from '/scripts/image-command-handler.js';

    const btn       = document.getElementById('processBtn');
    const imgEl     = document.getElementById('preview');

    function log(msg) { console.log(msg); }

    btn.addEventListener('click', () => {
      const client = new AvatarClient(window.location.origin, 'default');
      const dispatcher = new Dispatcher(client, 1);
      new ImageCommandHandler(dispatcher, imgEl);
      dispatcher.start();
    });
  </script>
</body>
</html>
'''