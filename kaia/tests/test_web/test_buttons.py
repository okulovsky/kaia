from unittest import TestCase
from dataclasses import dataclass
from typing import Any
import base64

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from avatar.services import ButtonGrid, ButtonPressedEvent
from kaia.tests.test_web.environment import TestEnvironmentFactory



class ButtonGridHandlerTestCase(TestCase):
    def test_button_clicks_send_events(self):
        with TestEnvironmentFactory(HTML, aliases=dict(ButtonPressedEvent=ButtonPressedEvent)) as env:
            client = env.client
            driver = env.driver
            address = f'http://{env.api.address}'

            # 1) build a 2x2 grid: two clickable, one disabled
            builder = ButtonGrid.Builder(column_count=2)
            builder.add("Yes",  "yes_feedback")
            builder.add("No",   "no_feedback")
            builder.add("Skip", None)            # this button will be disabled
            grid = builder.to_grid()
            client.put(grid)

            messages = client.pull()



            # 2) open page and start dispatcher
            base_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "baseUrl"))
            )
            base_input.clear()
            base_input.send_keys(address)
            driver.find_element(By.ID, "processBtn").click()

            # 3) wait for buttons to render
            WebDriverWait(driver, 100).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#buttonOverlay button"))
            )
            buttons = driver.find_elements(By.CSS_SELECTOR, "#buttonOverlay button")
            # we expect 3 buttons in order: Yes, No, Skip
            self.assertEqual(len(buttons), 3)

            # 4) the third (Skip) must be disabled
            skip_btn = buttons[2]
            self.assertTrue(skip_btn.get_attribute("disabled") in ("true", "disabled"))


            # 5) click the first two
            buttons[0].click()

            messages = client.pull()
            self.assertEqual(1, len(messages))
            self.assertIsInstance(messages[0], ButtonPressedEvent)
            self.assertEqual('yes_feedback', messages[0].button_feedback)

            buttons[1].click()
            messages = client.pull()
            self.assertEqual(1, len(messages))
            self.assertIsInstance(messages[0], ButtonPressedEvent)
            self.assertEqual('no_feedback', messages[0].button_feedback)


HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ButtonGrid Test</title></head>
<body>
  <label for="baseUrl">Base URL:</label>
  <input id="baseUrl" value="http://localhost:8000" />
  <button id="processBtn">Start</button>
  <div id="buttonOverlay"></div>
  <script type="module">
    import { AvatarClient }      from './scripts/client.js';
    import { Dispatcher }        from './scripts/dispatcher.js';
    import { ButtonGridHandler } from './scripts/button-grid-handler.js';

    const baseInput = document.getElementById('baseUrl');
    const startBtn  = document.getElementById('processBtn');
    const overlay   = document.getElementById('buttonOverlay');

    startBtn.addEventListener('click', () => {
      const client     = new AvatarClient(baseInput.value, 'default');
      const dispatcher = new Dispatcher(client, 1);
      new ButtonGridHandler(dispatcher, overlay, client);
      dispatcher.start();
    });
  </script>
</body>
</html>
'''