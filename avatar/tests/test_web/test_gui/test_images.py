from avatar.utils.web_test_environment import WebTestEnvironmentFactory
from unittest import TestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from avatar.daemon import ImageCommand


class ImageHandlerTestCase(TestCase):
    def test_image_handler(self):
        with WebTestEnvironmentFactory(HTML) as env:
            png_bytes = b'\x89PNG\r\n\x1a\n'
            env.api.cache.upload('test.png', png_bytes)
            env.client.push(ImageCommand('test.png'))

            env.driver.find_element(By.ID, "processBtn").click()

            expected_src = '/cache/open/test.png'
            WebDriverWait(env.driver, 10).until(
                lambda d: d.find_element(By.ID, "preview").get_attribute("src") and
                          d.find_element(By.ID, "preview").get_attribute("src").endswith(expected_src)
            )


HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ImageCommand Test</title></head>
<body>
  <button id="processBtn">Start</button>
  <img id="preview" />
  <script type="module">
    import { AvatarClient, Dispatcher, ImageCommandHandler } from '/frontend/scripts/kaia-frontend.js';

    const btn   = document.getElementById('processBtn');
    const imgEl = document.getElementById('preview');

    btn.addEventListener('click', () => {
      const client     = new AvatarClient({baseUrl: window.location.origin});
      const dispatcher = new Dispatcher(client);
      new ImageCommandHandler({ dispatcher, imgEl });
      dispatcher.start();
    });
  </script>
</body>
</html>
'''
