from unittest import TestCase
from brainbox.tests.test_common.test_marshalling.marshalling_endpoint_structure import MyApi, Buffer
import requests

class MarhsallingTestCase(TestCase):
    def test_api(self):
        with MyApi.Test() as api:
            self.assertEqual("Hello, Test", api.hello('Test'))
            self.assertEqual(6, api.sum(5))
            self.assertEqual(7, api.sum(5, 2))
            self.assertEqual('test', api.custom_type('test').data)
            self.assertEqual('test', api.custom_type(Buffer('test')).data.data)
            self.assertRaises(Exception, lambda: api.throwing())
            self.assertEqual('custom_url test', api.custom_url('test'))


            reply = requests.get(f'http://{api.address}/hello', json=dict(s='Test'))
            self.assertEqual(
                'Hello, Test',
                reply.json()['result']
            )

            reply = requests.post(f'http://{api.address}/my/custom/url', json=dict(s='Test'))
            self.assertEqual(
                'custom_url Test',
                reply.json()['result']
            )



