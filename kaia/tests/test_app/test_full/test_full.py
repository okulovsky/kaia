import time
from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.services import *
from kaia.tests.helper import Helper, SeleniumDriver
from kaia.app import ServerStartedEvent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By



class FullTestCase(TestCase):
    def test_ping(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            helper = Helper(folder, self, True)
            with helper.app.get_fork_app(None):
                helper.init()
                helper.client.put(ChatCommand("Test"))
                with SeleniumDriver(helper.app.avatar_api, True) as driver:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#chat p"))
                    )

                    # Gather rendered <p> elements
                    paras = driver.find_elements(By.CSS_SELECTOR, "#chat p")
                    self.assertEqual(len(paras), 1) #Checking that "Test" ChatCommand is not in fact in the chat
                    self.assertIn("Nice to see you!", paras[0].get_attribute("innerHTML"))

                    reply_1 = helper.parse_reaction(TextCommand)

                    helper.wakeword()
                    helper.say('are_you_here')
                    reply_2 = helper.parse_reaction(UtteranceSequenceCommand)

                    paras = driver.find_elements(By.CSS_SELECTOR, "#chat p")
                    self.assertEqual(len(paras), 3)

                    helper.client.put(ServerStartedEvent())
                    helper.client.query(10).where(lambda z: isinstance(z, InitializationEvent)).first()


