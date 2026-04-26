from foundation_kaia.releasing.mddoc import *

"""
## Marshalling

Submodule `marshalling` organizes remote procedure call for python code via HTTP/websockets protocol and simple
comminucation format that is easy to reproduce outside of python.

### Essentials

`marshalling` starts with defining the interface with the desired functionality:

"""
from foundation_kaia.marshalling import service, endpoint
from typing import Any

@service
class IMyService:
    @endpoint
    def select(self, id: str, data: list[dict[str, Any]], drop_duplicates: bool|None = None) -> list[str]:
        ...

"""
This interface needs to be implemented in the service:
"""

class MyService(IMyService):
    def select(self, id: str, data: list[dict[str, Any]], drop_duplicates: bool|None = None) -> list[str]:
        result = []
        for element in data:
            if element['id'] == id:
                if drop_duplicates and element['text'] in result:
                    continue
                result.append(element['text'])
        return result

"""
This is enough to create a web-server that will serve `MyService`, exposing it's methods (marked with `@endpoint`)
as the server's endpoints. Also, you can create an API that will implement `IMyService`, therefore providing a direct
replacement for the direct call of `IMyService` methods:  
"""

from foundation_kaia.marshalling import ApiCall, Server, ServiceComponent, ApiUtils
from foundation_kaia.fork import Fork

PORT = 14000

class MyApi(IMyService):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, IMyService)

expected_result = ControlValue.mddoc_define_control_value(["example 1", "example 2"])

if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(MyService()))

    with Fork(server):
        base_url = f"http://localhost:{PORT}"
        ApiUtils.wait_for_reply(base_url, 10)
        api = MyApi(base_url)
        result = api.select(
            'test',
            [
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test', 'text': 'example 2'},
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test_1', 'text': 'example 3'},
            ],
            True
        )

        """
        After this, `result` will be:
        """

        expected_result.mddoc_validate_control_value(result)

"""
### Calling server outside of Python

The server can be called without API and python, as a plain HTTP server. The parameters should be passed as:

* primitives, non-nullable: as a part of the url path in the order of appearence in the method
* primitives, nullable: as a part of the query string
* others: in JSON body. 

If you do not wish these complications, you may use `force_json_params` parameter of `@endpoint` decorator.

Now, let's call out server:

"""
import requests


if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(MyService()))

    with Fork(server):
        ApiUtils.wait_for_reply(f"http://localhost:{PORT}", 10)
        response = requests.post(
            f"http://localhost:{PORT}/my-service/select/test/?drop_duplicates=True",
            json=dict(data=[
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test', 'text': 'example 2'},
                {'id': 'test', 'text': 'example 1'},
                {'id': 'test_1', 'text': 'example 3'},
            ]))
        response.raise_for_status()

        """
        `response.json()` will be:
        """

        expected_result.mddoc_validate_control_value(response.json())

"""
To get a reference of the services, endpoints, as well as JsonSchema for the passing jsons, please use this: 

"""
from foundation_kaia.marshalling.documenter import ApiDocumentation

from foundation_kaia.marshalling.documenter import *; expected_documentation = ControlValue.mddoc_define_control_value(EndpointDocumentation(name='select', docstring=None, url_template='/my-service/select/<id>?drop_duplicates=<drop_duplicates>', json_schema=JsonSchema(schema={'type': 'object', 'properties': {'data': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': {}}}}}, defs={}), file_params=[], return_type='list', return_is_file=False))

documentation = ApiDocumentation.parse(MyApi)

"""
For instance, `documentation.services['my-service'].endpoints['select']` is:
"""

expected_documentation.mddoc_validate_control_value(ApiDocumentation.parse(MyApi).services['my-service'].endpoints['select'])

