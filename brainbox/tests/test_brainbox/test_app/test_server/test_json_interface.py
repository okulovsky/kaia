from brainbox import BrainBoxApi
from unittest import TestCase
import requests
import json

class JsonInterfaceTestCase(TestCase):
    def test_json_interface(self):
        with BrainBoxApi.Test() as api:
            job = dict(
                id='test',
                decider='FakeFile',
                method=None,
                arguments=dict(
                    tags=dict(test='test'),
                    array_length=3
                )
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

            result = reply.json()['result'][0]
            for i,file in enumerate(result):
                reply = requests.get(f'http://{api.address}/cache/download/{file}')
                js = json.loads(reply.text)
                self.assertDictEqual(dict(test='test', option_index=i), js)

