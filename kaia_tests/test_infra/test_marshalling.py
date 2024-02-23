from unittest import TestCase
from kaia.infra import MarshallingEndpoint, Loc
from kaia.infra.app import KaiaApp, SubprocessRunner
from dataclasses import dataclass
import flask
from yo_fluq_ds import *

class API:
    test_1 = MarshallingEndpoint('/test/1', 'POST')
    test_2 = MarshallingEndpoint('/test/2', 'GET')

@dataclass
class TestInput:
    s: str
    i: int

@dataclass
class TestOutput:
    result: str



class Server:
    def __init__(self, errors_folder):
        self.errors_folder = errors_folder

    def __call__(self):
        self.app = flask.Flask('test')
        binder = MarshallingEndpoint.Binder(self.app, self.errors_folder)
        binder.bind_all(API, self)
        self.app.run('0.0.0.0', 8999)

    def test_1(self, argument: TestInput):
        if argument.i % 2 == 0:
            raise ValueError('Deny')
        return TestOutput(f'1-{argument.s}-{argument.i}')

    def test_2(self, arg_1, arg_2):
        return TestOutput(f'2-{arg_1}-{arg_2}')


class MarshallingTestCase(TestCase):
    def test_marshalling(self):
        with Loc.create_temp_folder('mashalling_test') as folder:
            server = Server(folder)
            app = KaiaApp()
            app.add_runner(SubprocessRunner(server, 5))
            app.run_services_only()

            address = '127.0.0.1:8999'
            caller = MarshallingEndpoint.Caller(address)
            result = caller.call(API.test_1, TestInput('x',1))
            self.assertEqual('1-x-1', result.result)

            result = caller.call(API.test_2, 'ab', 'cd')
            self.assertEqual('2-ab-cd', result.result)

            result = caller.call(API.test_2, arg_1 = 'abx', arg_2 = 'cdx')
            self.assertEqual('2-abx-cdx', result.result)

            self.assertRaises(Exception, lambda: caller.call(API.test_1, TestInput('x', 2)))
            file = Query.folder(folder).single()
            self.assertSetEqual({'exception', 'input', 'endpoint'}, set(FileIO.read_json(file)))



