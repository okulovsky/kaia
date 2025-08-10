import time
from kaia.tests.test_web.environment import TestEnvironmentFactory
from unittest import TestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass
from avatar.messaging import IMessage, Confirmation


@dataclass
class TestInput(IMessage):
    field: str = ''

@dataclass
class TestReply(IMessage):
    pass


class MessagingTestCase(TestCase):

    def test_message_count(self):

        with TestEnvironmentFactory(HTML_COUNT, headless=False) as env:
            # Put one message in the queue
            env.client.put(TestInput())

            count_btn = env.driver.find_element(By.ID, "countBtn")
            count_display = env.driver.find_element(By.ID, "countDisplay")

            # First click: should fetch one message
            count_btn.click()
            WebDriverWait(env.driver, 1).until(
                EC.text_to_be_present_in_element((By.ID, "countDisplay"), "Count: 1")
            )
            self.assertEqual(count_display.text, 'Count: 1')

            # Second click: no new messages
            count_btn.click()
            WebDriverWait(env.driver, 100).until(
                EC.text_to_be_present_in_element((By.ID, "countDisplay"), "Count: 0")
            )
            self.assertEqual(count_display.text, 'Count: 0')



HTML_COUNT = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Message Count</title>
</head>
<body>
  <h1>Message Count</h1>
  <button id="countBtn">Get Message Count</button>
  <div id="countDisplay">Count: 0</div>

  <script type="module">
    import { AvatarClient } from '/scripts/client.js';

    const countBtn = document.getElementById('countBtn');
    const display = document.getElementById('countDisplay');
    const client = new AvatarClient(window.location.origin);

    countBtn.addEventListener('click', async () => {
      try {
        const messages = await client.getMessages();
        display.textContent = `Count: ${messages.length}`;
      } catch (error) {
        console.error(error);
        display.textContent = `Error: ${error.message}`;
      }
    });
  </script>
</body>
</html>
'''
