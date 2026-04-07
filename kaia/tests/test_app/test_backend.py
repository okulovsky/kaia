from unittest import TestCase
from avatar.daemon import *
from kaia.utils import BackendTestEnvironmentFactory
from yo_fluq import Query
from loguru import logger
from kaia.skills.ping import PingIntents
from kaia.skills.time import TimeIntents
from kaia.skills.echo_skill import EchoIntents



class BackendInitializationTestCase(TestCase):
    def test_initialization_event(self):
        with BackendTestEnvironmentFactory(self) as env:
            env.client.scroll_to_end()

            logger.info("INITIALIZATION")
            env.client.push(InitializationEvent())
            reaction = env.parse_reaction(TextCommand)
            self.assertFalse(Query.en(reaction).where(lambda z: isinstance(z, ExceptionEvent)).any())

            logger.info("FIRST COMMAND: PING")

            env.client.push(TextEvent(PingIntents.question()))
            env.parse_reaction(TextCommand)

            logger.info("SECOND COMMAND: TIME")

            env.client.push(TextEvent(TimeIntents.question()))
            env.parse_reaction(TextCommand)

            logger.info("THIRD COMMAND: ECHO")

            env.client.push(TextEvent(EchoIntents.echo()))
            env.parse_reaction(TextCommand)

            env.client.push(TextEvent("Make me a sandwich"))
            env.parse_reaction(TextCommand)
