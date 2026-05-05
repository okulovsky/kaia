from unittest import TestCase
from foundation_kaia.fork import Fork
from foundation_kaia.marshalling import ApiUtils
import requests
import time
import uvicorn
from fastapi import FastAPI

class Server:
    def __call__(self):
        app = FastAPI()
        app.add_api_route('/', self.index, methods=['GET'])
        uvicorn.run(app, host='127.0.0.1', port=8099)

    def index(self):
        return 'OK'


def error():
    print("Test1")
    time.sleep(0.3)
    raise ValueError("Error")


class ForkTestCase(TestCase):
    def test_fork(self):
        Fork(Server()).start()
        ApiUtils.wait_for_reply('http://127.0.0.1:8099', 5)


    def test_erroneous_fork(self):
        Fork(error).start()
        print('OK')
        time.sleep(2)



