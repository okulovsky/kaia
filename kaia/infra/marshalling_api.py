import os
import time
from typing import *
import dataclasses
import re
import requests
import flask
from pathlib import Path
import traceback
from .file_io import FileIO
from datetime import datetime
from uuid import uuid4
import base64
import pickle
import io
from .app import KaiaApp
from typing import TypeVar, Generic



class _MarshallingExecutor:
    def __init__(self,
                 endpoint: 'MarshallingEndpoint',
                 function: Callable,
                 folder: Path,
                 ):
        self.endpoint = endpoint
        self.function = function
        self.folder = folder
        self.__name__ = endpoint.endpoint

    def __call__(self):
        binary = flask.request.data
        try:
            argument = pickle.loads(flask.request.data)
            result = self.function(*argument['args'], **argument['kwargs'])
        except:
            report = dict(
                endpoint=self.endpoint.endpoint,
                exception=traceback.format_exc(),
                input=base64.b64encode(binary).decode('utf-8')
            )
            if self.folder is not None:
                os.makedirs(self.folder, exist_ok=True)
                FileIO.write_json(report, self.folder/f'{str(datetime.now()).replace(":","-")}-{uuid4()}.json')
            return flask.jsonify(report), 500
        bytes = pickle.dumps(result)
        return flask.send_file(
            io.BytesIO(bytes),
            mimetype='binary/octet-stream'
        )


@dataclasses.dataclass
class MarshallingEndpoint:
    endpoint: str
    method: str = 'POST'

    @staticmethod
    def check_address(address):
        if not re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', address):
            raise ValueError(f'Address must be IP:port, no protocol, no trailing slash, but was:\n{address}')

    @dataclasses.dataclass
    class Binder:
        app: flask.Flask
        errors_folder: Optional[Path] = None

        def bind(self, endpoint: 'MarshallingEndpoint', function):
            self.app.add_url_rule(
                endpoint.endpoint,
                methods=[endpoint.method],
                view_func=_MarshallingExecutor(endpoint, function, self.errors_folder)
            )

        def _heartbeat(self):
            return 'OK'

        def bind_all(self, endpoints_class: Type, functions_obj):
            for field in vars(endpoints_class):
                obj = getattr(endpoints_class, field)
                if isinstance(obj, MarshallingEndpoint):
                    self.bind(obj, getattr(functions_obj, field))
            self.app.add_url_rule(
                '/heartbeat',
                methods=['GET'],
                view_func=self._heartbeat
            )

    class Caller:
        def __init__(self, address: str):
            MarshallingEndpoint.check_address(address)
            self.address = address

        def call(self, endpoint: 'MarshallingEndpoint',  *args, **kwargs):
            argument = dict(args=args, kwargs=kwargs)
            data = pickle.dumps(argument)
            callable_method = getattr(requests, endpoint.method.lower())
            reply = callable_method(
                f'http://{self.address}{endpoint.endpoint}',
                data=data,
                headers={'Content-Type': 'binary/octet-stream'}
            )
            if reply.status_code != 200:
                exc = None
                try:
                    exc = reply.json()['exception']
                except:
                    pass
                if exc is not None:
                    raise ValueError(f'Endpoint {endpoint.endpoint} returned status_code {reply.status_code}. Exception:\n{exc}')
                else:
                    raise ValueError(f'Endpoint {endpoint.endpoint} returned status_code {reply.status_code}.\n{reply.text}')
            return pickle.loads(reply.content)


    class API:
        def __init__(self, address: str):
            self.address = address
            self.caller = MarshallingEndpoint.Caller(address)

        def check_availability(self):
            try:
                result = requests.get(f'http://{self.caller.address}/heartbeat')
                if result.status_code == 200:
                    return True
            except:
                return False

        def wait_for_availability(self, time_in_seconds: int|None = None):
            begin = datetime.now()
            while True:
                if self.check_availability():
                    return
                time.sleep(0.1)
                if time_in_seconds is not None:
                    if (datetime.now() - begin).seconds > time_in_seconds:
                        raise ValueError("Couldn't wait for server to start")


    class TestAPI:
        def _prepare_service(self, api, service, seconds_to_wait: int = 5):
            self.app = KaiaApp()
            self.app.add_subproc_service(service)
            self.app.run_services_only()
            api.wait_for_availability(seconds_to_wait)
            return api

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.app.exit()

