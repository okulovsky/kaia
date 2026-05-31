from foundation_kaia.releasing.mddoc import *

"""

### Files

Marshalling can handle incoming files in two different ways:

* Normal files: collected in the buffer at the server's side, and then delivered to the method as blob of bytes. The arguments that have `bytes` in their type annotation will be such normal files. The more practical way is to use `FileLike` annotation, that allows you to send Path, str, bytes and `File` objects.
* Streams: transfered bit-by-bit and delivered to the method as `Iterable[bytes]`, so they can be processed bit by bit. The arguments with Iterable[bytes] in their annotation will be streaming files. Iterable[bytes]|FileLike is also a streaming file.

Depending on the combination of the arguments, following structures in the requests' body are possible:

* Only json-parameters, no file: the body will be JSON (Content-Type will be set application/json)
* A single file, normal or stream: the body will be this file (Content-Type will be set to application/octet-stream)
* A mix of normal files and json-parameters: multipart-form containing `json_arguments` part with json and the files
* Other combinations are not possible in HTTP protocol, but can be used in WebSockets. Also, the structure when the endpoint consumes a file bit-by-bit and produces the output file bit-by-bit, is not possible in HTTP protocol.

If the output of the endpoint is file, it is always streamed.

Let's define a service that demonstrates all the HTTP-compatible combinations, using them with `requests` library. API doesn't really need an additional demonstration as all of these cases are processed under the hood with API remaning the drop-in replacement for the service in the codebase.

We will use `force_json_params=True` to ensure the arguments end up in the JSON, not in the query params or url.

We will also use `verify_abstract=False` argument to merge interface with the service. It's not normally needed as the clear separation between the interface and the service is important, but in the testing environment, it's handy to unite them in one class.

`FileLikeHandler` is a type-hint-friendly and convenient class that will transform all the files to the bytes at the server's side.   

"""

from foundation_kaia.marshalling import service, endpoint, FileLike, FileLikeHandler
from collections.abc import Iterable

@service
class IFileService:
    @endpoint(force_json_params=True, verify_abstract=False)
    def json_only(self, name: str) -> str:
        return name

    @endpoint(verify_abstract=False)
    def single_file(self, file: FileLike|Iterable[bytes]) -> int:
        return len(FileLikeHandler.to_bytes(file))

    @endpoint(force_json_params=True, verify_abstract=False)
    def json_and_file(self, name: str, file: FileLike) -> int:
        return len(FileLikeHandler.to_bytes(file))

    @endpoint(force_json_params=True, verify_abstract=False)
    def download_file(self, content: str) -> Iterable[bytes]:
        encoded = content.encode('utf-8')
        chunk_size = 4
        for i in range(0, len(encoded), chunk_size):
            yield encoded[i:i + chunk_size]

"""
Now let's run the server and call each endpoint with `requests` to see the body structures.
"""

import json
import requests
from foundation_kaia.marshalling import Server, ServiceComponent, ApiUtils
from foundation_kaia.fork import Fork

PORT = 14010

json_only_result = ControlValue.mddoc_define_control_value("hello")
file_result = ControlValue.mddoc_define_control_value(5)
download_result = ControlValue.mddoc_define_control_value(b"hello")

if __name__ == '__main__':
    server = Server(PORT, ServiceComponent(IFileService()))

    with Fork(server):
        ApiUtils.wait_for_reply(f"http://localhost:{PORT}", 10)

        """
        JSON-only: the data sent is a JSON with the required arguments.
        """

        response = requests.post(
            f"http://localhost:{PORT}/file-service/json-only",
            json={"name": "hello"},
        )
        response.raise_for_status()

        """
        `response.json()` is:
        """

        json_only_result.mddoc_validate_control_value(response.json())

        """
        Single file / stream:
        """

        response = requests.post(
            f"http://localhost:{PORT}/file-service/single-file",
            data=b"hello",
        )
        response.raise_for_status()

        """
        `response.json()` is the total byte count:
        """

        file_result.mddoc_validate_control_value(response.json())

        """
        JSON and file
        """

        response = requests.post(
            f"http://localhost:{PORT}/file-service/json-and-file",
            files=[
                ('json_arguments', json.dumps({"name": "report"})),
                ('file', b'hello'),
            ],
        )
        response.raise_for_status()

        """
        `response.json()` is:
        """

        file_result.mddoc_validate_control_value(response.json())

        """
        Downloading a file: the response body is a stream of bytes regardless of how many chunks
        the server yields. Use `stream=True` and `iter_content` to consume it, or simply read
        `response.content` to collect everything at once.
        """

        response = requests.post(
            f"http://localhost:{PORT}/file-service/download-file",
            json={"content": "hello"},
            stream=True,
        )
        response.raise_for_status()

        """
        `response.content` reassembles all chunks into the original bytes:
        """

        download_result.mddoc_validate_control_value(response.content)
