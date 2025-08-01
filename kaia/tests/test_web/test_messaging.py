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
    def test_messaging(self):
        with TestEnvironmentFactory(HTML, aliases=dict(TestReply = TestReply, Confirmation = Confirmation)) as env:
            env.client.put(TestInput())

            base_input = WebDriverWait(env.driver, 10).until(
                EC.presence_of_element_located((By.ID, "baseUrl"))
            )
            base_input.clear()
            base_input.send_keys(f'http://{env.api.address}')
            print('base_input is set')

            # 3) Click the \"Fetch & Process\" button
            process_btn = env.driver.find_element(By.ID, "processBtn")
            process_btn.click()
            print('button is clicked')

            # 4) Wait until the log shows that messages were fetched
            WebDriverWait(env.driver, 100).until(
                EC.text_to_be_present_in_element(
                    (By.ID, "log"),
                    "Sent confirmation"
                )
            )
            messages = env.client.pull()
            self.assertIsInstance(messages[0], TestInput)
            self.assertIsInstance(messages[1], TestReply)
            self.assertEqual(messages[0].envelop.id, messages[1].envelop.reply_to)
            self.assertEqual('console', messages[1].envelop.publisher)

            self.assertIsInstance(messages[2], Confirmation)
            self.assertEqual((messages[0].envelop.id,), messages[2].envelop.confirmation_for)
            self.assertEqual('console', messages[2].envelop.publisher)



HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TestInput Processor</title>
</head>
<body>
  <h1>TestInput Processor</h1>
  <label for="baseUrl">API Base URL:</label>
  <input id="baseUrl" type="text" value="http://localhost:8000" />
  <button id="processBtn">Fetch & Process</button>
  <div id="log"></div>

  <script type="module">
    import { Message } from './scripts/message.js';
    import { AvatarClient } from './scripts/client.js';

    const baseUrlInput = document.getElementById('baseUrl');
    const processBtn = document.getElementById('processBtn');
    const logContainer = document.getElementById('log');

    /** Append a message to the log area */
    function logMessage(text) {
      const p = document.createElement('p');
      p.textContent = text;
      logContainer.appendChild(p);
    }

    processBtn.addEventListener('click', async () => {
      logContainer.innerHTML = '';
      const baseUrl = (baseUrlInput.value || '').trim();
      if (!baseUrl) {
        logMessage('Please provide a valid base URL.');
        return;
      }
      const client = new AvatarClient(baseUrl);

      try {
        const messages = await client.getMessages();
        logMessage(`Fetched ${messages.length} messages.`);

        for (const msg of messages) {
          logMessage(`Message: type=${msg.message_type}, id=${msg.envelop.id}`);
          if (msg.message_type.endsWith('/TestInput')) {
            // Create and send a reply message
            const reply = new Message('TestReply');
            reply.asReplyTo(msg);
            await client.addMessage(reply);
            logMessage(`Sent reply to ${msg.envelop.id}`);

            // Create and send a confirmation message
            const confirmation = new Message('Confirmation');
            confirmation.asConfirmationFor(msg);
            await client.addMessage(confirmation);
            logMessage(`Sent confirmation for ${msg.envelop.id}`);
          }
        }
      } catch (error) {
        console.error(error);
        logMessage(`Error: ${error.message}\n${error.stack}`);
      }
    });
  </script>
</body>
</html>
'''