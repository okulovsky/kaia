import unittest
from collections.abc import Iterable
from dataclasses import dataclass

import requests

from foundation_kaia.marshalling import (
  ApiError, endpoint, FileLike, service, Server, ServiceComponent, ApiCall, TestApi
)


PORT = 8895


@dataclass
class Data:
    value: int


@service
class ErrorImpl:
    # --- path / query parse errors ---

    @endpoint(verify_abstract=False)
    def int_in_path(self, id: int) -> str:
        return f"id={id}"

    @endpoint(verify_abstract=False)
    def bool_in_query(self, flag: bool | None = None) -> str:
        return f"flag={flag}"

    # --- json body error (wrong type sent) ---

    @endpoint(verify_abstract=False)
    def json_body(self, data: Data) -> str:
        return f"value={data.value}"

    # --- file body error (sent as wrong content-type) ---

    @endpoint(verify_abstract=False)
    def file_body(self, f: FileLike) -> str:
        return f"len={len(f)}"

    # --- streaming output errors ---

    @endpoint(verify_abstract=False)
    def download_error_before(self) -> Iterable[bytes]:
        raise ValueError("error before first chunk")
        yield  # makes this a generator

    @endpoint(verify_abstract=False)
    def download_error_after(self) -> Iterable[bytes]:
        yield b'first chunk'
        raise ValueError("error after first chunk")

    # --- streaming input error ---

    @endpoint(verify_abstract=False)
    def upload_error(self, data: Iterable[bytes]) -> None:
        for _ in data:
            raise ValueError("error during upload")


class ErrorServer(Server):
    def __init__(self, port: int):
        super().__init__(port, ServiceComponent(ErrorImpl()))


class ErrorApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        ApiCall.define_endpoints(self, base_url, ErrorImpl)

    @staticmethod
    def test() -> 'TestApi[ErrorApi]':
        return TestApi(ErrorApi, ErrorServer(PORT))


class TestErrors(unittest.TestCase):

    # --- path / query parse errors → 400 ---

    def test_invalid_path_param_returns_400(self):
        with ErrorApi.test() as api:
            response = requests.post(f'{api.base_url}/error-impl/int-in-path/not-an-int')
            self.assertEqual(400, response.status_code)

    def test_invalid_query_param_returns_400(self):
        with ErrorApi.test() as api:
            response = requests.post(f'{api.base_url}/error-impl/bool-in-query?flag=not_a_bool')
            self.assertEqual(400, response.status_code)

    # --- json / file body errors → 500 (malformed body reaches service) ---

    def test_json_body_wrong_content_type_returns_error(self):
        with ErrorApi.test() as api:
            # Send JSON body with wrong content-type: server gets empty json_params
            response = requests.post(
                f'{api.base_url}/json_body',
                data=b'{"data": {"value": 1}}',
                headers={'Content-Type': 'text/plain'},
            )
            self.assertNotEqual(200, response.status_code)

    def test_file_body_wrong_content_type_returns_error(self):
        with ErrorApi.test() as api:
            # Send file with JSON content-type: server tries to parse as JSON → error
            response = requests.post(
                f'{api.base_url}/file_body',
                data=b'\x00\x01\x02',
                headers={'Content-Type': 'application/json'},
            )
            self.assertNotEqual(200, response.status_code)

    # --- streaming output errors ---

    def test_error_before_first_chunk_returns_500(self):
        with ErrorApi.test() as api:
            with self.assertRaises(ApiError) as ctx:
                api.download_error_before()
            self.assertEqual(500, ctx.exception.response.status_code)
            self.assertIn("error before first chunk", str(ctx.exception))

    def test_error_after_first_chunk_is_lost(self):
        with ErrorApi.test() as api:
            result = api.download_error_after()
            received = b''
            try:
                for chunk in result:
                    received += chunk
            except Exception:
                pass  # connection drop is expected; error details are lost
            self.assertEqual(b'first chunk', received)

    # --- streaming input error → 500 ---

    def test_error_during_upload_returns_500(self):
        with ErrorApi.test() as api:
            with self.assertRaises(ApiError) as ctx:
                api.upload_error(iter([b'chunk1', b'chunk2']))
            self.assertEqual(500, ctx.exception.response.status_code)
            self.assertIn("error during upload", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
