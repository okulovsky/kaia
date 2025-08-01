from unittest import TestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from avatar.services import ChatCommand, ChatMessageType
from kaia.tests.test_web.environment import TestEnvironmentFactory



class ChatHandlerTestCase(TestCase):
    def test_chat_handler_renders_different_types(self):
        # Arrange: set up test environment
        with TestEnvironmentFactory(HTML) as env:
            client = env.client
            driver = env.driver
            addr   = f'http://{env.api.address}'

            # Act: enqueue three ChatCommand messages
            client.put(ChatCommand(
                text="Hello\nWorld",
                type=ChatMessageType.from_user,
                sender_avatar_file_id="/avatar.png"
            ))
            client.put(ChatCommand(
                text="System message",
                type=ChatMessageType.system
            ))
            client.put(ChatCommand(
                text="Oops, error!",
                type=ChatMessageType.error
            ))

            # Open page, fill baseUrl, click Start
            base_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "baseUrl"))
            )
            base_input.clear()
            base_input.send_keys(addr)
            driver.find_element(By.ID, "processBtn").click()

            # Assert: wait until at least one message rendered
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#chat p"))
            )

            # Gather rendered <p> elements
            paras = driver.find_elements(By.CSS_SELECTOR, "#chat p")
            self.assertEqual(len(paras), 3)

            # 1) from_user: right, newline→<br>, avatar style
            p1 = paras[0]
            self.assertEqual(p1.get_attribute("class"), "right")
            self.assertIn("Hello<br>World", p1.get_attribute("innerHTML"))
            style1 = p1.get_attribute("style")
            self.assertIn("background-image", style1)

            # 2) system: center + italic
            p2 = paras[1]
            self.assertEqual(p2.get_attribute("class"), "center")
            style2 = p2.get_attribute("style")
            self.assertIn("font-style: italic", style2)
            self.assertIn("System message", p2.get_attribute("innerHTML"))

            # 3) error: left + monospace
            p3 = paras[2]
            self.assertEqual(p3.get_attribute("class"), "left")
            style3 = p3.get_attribute("style")
            self.assertIn("font-family: monospace", style3)
            self.assertIn("Oops, error!", p3.get_attribute("innerHTML"))



HTML = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Chat Test</title></head>
<body>
  <label for="baseUrl">Base URL:</label>
  <input id="baseUrl" value="http://localhost:8000" />
  <button id="processBtn">Start</button>
  <div id="chat"></div>
  <script type="module">
    import { AvatarClient } from './scripts/client.js';
    import { Dispatcher }   from './scripts/dispatcher.js';
    import { ChatHandler }  from './scripts/chat-handler.js';
    const baseInput = document.getElementById('baseUrl');
    const btn       = document.getElementById('processBtn');
    const chatDiv   = document.getElementById('chat');
    btn.addEventListener('click', () => {
      const client     = new AvatarClient(baseInput.value, 'default');
      const dispatcher = new Dispatcher(client, 1);
      new ChatHandler(dispatcher, chatDiv, baseInput.value);
      dispatcher.start();
    });
  </script>
</body></html>
'''