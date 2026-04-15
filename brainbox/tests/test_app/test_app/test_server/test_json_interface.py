from unittest import TestCase
import requests

from brainbox.framework.common import ISelfManagingDecider
from brainbox.framework.app.api import BrainBoxApi

PORT = 18194


class Empty(ISelfManagingDecider):
    def run(self):
        pass


class JsonInterfaceTestCase(TestCase):
    def test_json_interface(self):
        with BrainBoxApi.test([Empty()], port=PORT) as api:
            body = {
                "jobs": [
                    {
                        "id": "test",
                        "decider": "Empty",
                        "parameter": None,
                        "method": "run",
                        "arguments": {},
                        "info": None,
                        "batch": None,
                        "ordering_token": None,
                        "dependencies": {},
                    }
                ]
            }

            reply = requests.post(
                f'http://127.0.0.1:{PORT}/tasks-service/base-add',
                json=body,
            )
            if reply.status_code != 200:
                self.fail(f'base-add failed: {reply.text}')

            reply = requests.post(
                f'http://127.0.0.1:{PORT}/tasks-service/base-join',
                json={"ids": ["test"]},
            )
            if reply.status_code != 200:
                self.fail(f'base-join failed: {reply.text}')
