from unittest import TestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from avatar.daemon import ButtonGridCommand, ButtonPressedEvent
from avatar.utils.web_test_environment import WebTestEnvironmentFactory


class ButtonGridCommandHandlerTestCase(TestCase):
    def test_button_clicks_send_events(self):
        with WebTestEnvironmentFactory(HTML, aliases=dict(ButtonPressedEvent=ButtonPressedEvent)) as env:
            builder = ButtonGridCommand.Builder(column_count=2)
            builder.add("Yes",  "yes_feedback")
            builder.add("No",   "no_feedback")
            builder.add("Skip", None)
            env.client.push(builder.to_grid())
            env.client.pull(timeout_in_seconds=0)

            env.driver.find_element(By.ID, "processBtn").click()

            WebDriverWait(env.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#buttonOverlay button"))
            )
            buttons = env.driver.find_elements(By.CSS_SELECTOR, "#buttonOverlay button")
            self.assertEqual(len(buttons), 3)

            skip_btn = buttons[2]
            self.assertTrue(skip_btn.get_attribute("disabled") in ("true", "disabled"))

            buttons[0].click()
            messages = env.client.pull(timeout_in_seconds=2)
            self.assertEqual(1, len(messages))
            self.assertIsInstance(messages[0], ButtonPressedEvent)
            self.assertEqual('yes_feedback', messages[0].button_feedback)

            buttons[1].click()
            messages = env.client.pull(timeout_in_seconds=2)
            self.assertEqual(1, len(messages))
            self.assertIsInstance(messages[0], ButtonPressedEvent)
            self.assertEqual('no_feedback', messages[0].button_feedback)


HTML = '''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>ButtonGridCommand Test</title></head>
<body>
  <button id="processBtn">Start</button>
  <div id="buttonOverlay"></div>
  <script type="module">
    import { AvatarClient, Dispatcher, ButtonGridCommandHandler } from '/frontend/scripts/index.js';

    const startBtn = document.getElementById('processBtn');
    const overlay  = document.getElementById('buttonOverlay');

    startBtn.addEventListener('click', () => {
      const client     = new AvatarClient({baseUrl: window.location.origin});
      const dispatcher = new Dispatcher(client);
      new ButtonGridCommandHandler({ dispatcher, overlay, client });
      dispatcher.start();
    });
  </script>
</body>
</html>
'''
