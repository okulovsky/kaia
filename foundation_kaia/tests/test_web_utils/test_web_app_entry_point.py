from foundation_kaia.web_utils import WebAppEntryPoint
from foundation_kaia.marshalling import ApiUtils
from foundation_kaia.fork import Fork
import flask
from unittest import TestCase
import requests

PORT = 18023

class MyServer:
    def create_web_app_entry_point(self):
        app = flask.Flask(__name__)
        app.add_url_rule('/', view_func=self.index, methods=['GET'])
        ep = WebAppEntryPoint(app, PORT)
        return ep

    def index(self):
        return 'ok'


    def __call__(self):
        ep = self.create_web_app_entry_point()
        ep.run()


class WebServerForkTestCase(TestCase):
    def test_web_server_fork(self):

        with Fork(MyServer()):
            address = f"http://localhost:{PORT}/"
            ApiUtils.wait_for_reply(address, 5)
            reply = requests.get(address)
            self.assertEqual(200, reply.status_code)

