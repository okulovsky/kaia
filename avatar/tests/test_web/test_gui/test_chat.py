from unittest import TestCase

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from avatar.daemon import ChatCommand, ChatMessageType
from avatar.utils.web_test_environment import WebTestEnvironmentFactory


class ChatHandlerTestCase(TestCase):
    def test_chat_handler_renders_different_types(self):
        with WebTestEnvironmentFactory(HTML) as env:
            env.client.push(ChatCommand(
                text="Hello\nWorld",
                type=ChatMessageType.from_user,
                sender_avatar_file_id="/avatar.png"
            ))
            env.client.push(ChatCommand(
                text="System message",
                type=ChatMessageType.system
            ))
            env.client.push(ChatCommand(
                text="Oops, error!",
                type=ChatMessageType.error
            ))

            env.driver.find_element(By.ID, "processBtn").click()

            WebDriverWait(env.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#chat p"))
            )

            paras = env.driver.find_elements(By.CSS_SELECTOR, "#chat p")
            self.assertEqual(len(paras), 3)

            p1 = paras[0]
            self.assertEqual(p1.get_attribute("class"), "right")
            self.assertIn("Hello<br>World", p1.get_attribute("innerHTML"))
            self.assertIn("background-image", p1.get_attribute("style"))

            p2 = paras[1]
            self.assertEqual(p2.get_attribute("class"), "system")
            self.assertIn("System message", p2.get_attribute("innerHTML"))

            p3 = paras[2]
            self.assertEqual(p3.get_attribute("class"), "error")


HTML = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Chat Test</title></head>
<body>
  <button id="processBtn">Start</button>
  <div id="chat"></div>
  <script type="module">
    import { AvatarClient, Dispatcher, ChatCommandHandler } from '/frontend/scripts/index.js';
    const btn     = document.getElementById('processBtn');
    const chatDiv = document.getElementById('chat');
    btn.addEventListener('click', () => {
      const client     = new AvatarClient({baseUrl: window.location.origin});
      const dispatcher = new Dispatcher(client);
      new ChatCommandHandler({ dispatcher, container: chatDiv, baseUrl: window.location.origin });
      dispatcher.start();
    });
  </script>
</body></html>
'''
