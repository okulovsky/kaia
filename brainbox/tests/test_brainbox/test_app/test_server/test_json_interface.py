from brainbox import BrainBoxApi
from unittest import TestCase
import requests
import json

class JsonInterfaceTestCase(TestCase):
    def test_json_interface(self):
        with BrainBoxApi.Test() as api:
            job = dict(
                id='test',
                decider='Empty',
                method=None,
                arguments=dict()
            )

            js = dict(arguments=dict(jobs=[job]))

            requests.post(
                f'http://{api.address}/jobs/add',
                json=js
            )

            reply = requests.get(
                f'http://{api.address}/jobs/join',
                json = dict(arguments=dict(ids=['test']))
            )
            if reply.status_code!=200:
                print(reply.text)
                self.fail()
