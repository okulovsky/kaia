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
            self.assertEqual('test', api.custom_type_jsonpickle(Buffer('test')).data.data)
            self.assertRaises(Exception, lambda: api.throwing())
            self.assertEqual('custom_url test', api.custom_url('test'))


            reply = requests.get(f'http://{api.address}/hello', json=dict(arguments=dict(s='Test')))
            if reply.json()['error'] is not None:
                print(reply.json()['error'])
                self.fail()

            self.assertEqual(
                'Hello, Test',
                reply.json()['result']
            )

            reply = requests.post(f'http://{api.address}/my/custom/url', json=dict(arguments=dict(s='Test')))
            if reply.json()['error'] is not None:
                print(reply.json()['error'])
                self.fail()

            self.assertEqual(
                'custom_url Test',
                reply.json()['result']
            )

            reply = requests.post(f'http://{api.address}/custom_type_jsonpickle', json=dict(arguments=dict(data='test')))
            self.assertEqual('test', reply.json()['result']['@content']['data'])



