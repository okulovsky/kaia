import unittest
from collections.abc import Iterable

from foundation_kaia.marshalling import websocket, service, Server, ServiceComponent, ApiCall, TestApi


PORT = 8885


@service
class WsErrorImpl:
    # --- path / query parse errors ---

    @websocket(verify_abstract=False)
    def int_in_path(self, id: int) -> str:
        return f"id={id}"

    @websocket(verify_abstract=False)
    def bool_in_query(self, flag: bool | None = None) -> str:
        return f"flag={flag}"

    # --- streaming output errors ---

    @websocket(verify_abstract=False)
    def download_error_before(self) -> Iterable[bytes]:
        raise ValueError("error before first chunk")
        yield  # makes this a generator

    @websocket(verify_abstract=False)
    def download_error_after(self) -> Iterable[bytes]:
        yield b'first chunk'
        raise ValueError("error after first chunk")

    # --- streaming input error ---

    @websocket(verify_abstract=False)
    def upload_error(self, data: Iterable[bytes]) -> None:
        for _ in data:
            raise ValueError("error during upload")


class WsErrorServer(Server):
    def __init__(self, port: int):
        super().__init__(port, ServiceComponent(WsErrorImpl()))


class WsErrorApi(WsErrorImpl):
    def __init__(self, base_url: str):
        self.base_url = base_url
        ApiCall.define_endpoints(self, base_url, WsErrorImpl)

    @staticmethod
    def test() -> 'TestApi[WsErrorApi]':
        return TestApi(WsErrorApi, WsErrorServer(PORT))


class TestWsErrors(unittest.TestCase):

    # --- path / query parse errors ---

    def test_invalid_path_param_raises(self):
        with WsErrorApi.test() as api:
            import websocket as ws_client
            import json
            ws = ws_client.create_connection(f'ws://127.0.0.1:{PORT}/ws-error-impl/int-in-path/not-an-int')
            msg = json.loads(ws.recv())
            ws.close()
            self.assertEqual('error', msg['type'])

    def test_invalid_query_param_raises(self):
        with WsErrorApi.test() as api:
            import websocket as ws_client
            import json
            ws = ws_client.create_connection(f'ws://127.0.0.1:{PORT}/ws-error-impl/bool-in-query?flag=not_a_bool')
            msg = json.loads(ws.recv())
            ws.close()
            self.assertEqual('error', msg['type'])

    # --- streaming output errors ---

    def test_error_before_first_chunk_raises(self):
        with WsErrorApi.test() as api:
            with self.assertRaises(Exception) as ctx:
                api.download_error_before()
            self.assertIn("error before first chunk", str(ctx.exception))

    def test_error_after_first_chunk_is_reported(self):
        """Unlike HTTP, WebSocket properly reports errors that occur mid-stream."""
        with WsErrorApi.test() as api:
            result = api.download_error_after()
            received = b''
            with self.assertRaises(Exception) as ctx:
                for chunk in result:
                    received += chunk
            self.assertEqual(b'first chunk', received)
            self.assertIn("error after first chunk", str(ctx.exception))

    # --- streaming input error → error is sent back ---

    def test_error_during_upload_raises(self):
        with WsErrorApi.test() as api:
            with self.assertRaises(Exception) as ctx:
                api.upload_error(iter([b'chunk1', b'chunk2']))
            self.assertIn("error during upload", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
