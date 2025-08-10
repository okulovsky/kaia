from unittest import TestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from avatar.daemon import ChatCommand, ChatMessageType
from kaia.tests.test_web.environment import TestEnvironmentFactory



class ChatHandlerTestCase(TestCase):
    def test_chat_handler_renders_different_types(self):
        # Arrange: set up test environment
        with TestEnvironmentFactory(HTML, headless=True) as env:
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

            # 2) system
            p2 = paras[1]
            self.assertEqual(p2.get_attribute("class"), "system")
            self.assertIn("System message", p2.get_attribute("innerHTML"))

            # 3) error
            p3 = paras[2]
            self.assertEqual(p3.get_attribute("class"), "error")
            style3 = p3.get_attribute("style")



HTML = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Chat Test</title></head>
<body>
  <button id="processBtn">Start</button>
  <div id="chat"></div>
  <script type="module">
    import { AvatarClient } from '/scripts/client.js';
    import { Dispatcher }   from '/scripts/dispatcher.js';
    import { ChatCommandHandler }  from '/scripts/chat-command-handler.js';
    const btn       = document.getElementById('processBtn');
    const chatDiv   = document.getElementById('chat');
    btn.addEventListener('click', () => {
      const client     = new AvatarClient(window.location.origin, 'default');
      const dispatcher = new Dispatcher(client, 1);
      new ChatCommandHandler(dispatcher, chatDiv, window.location.origin);
      dispatcher.start();
    });
  </script>
</body></html>
'''