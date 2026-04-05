from collections.abc import Iterable
from unittest import TestCase

from foundation_kaia.marshalling_2.marshalling.model import EndpointModel, endpoint, websocket, FileLike, ResultType


class TestInputOutputTypeDetection(TestCase):

    # Input parameters.
    # If Iterable[bytes] appears anywhere in the union → binary_stream_param.
    # Otherwise, file-like types (bytes, str, Path, …) → file_params.

    def test_bytes_input_is_file_param(self):
        class Impl:
            @websocket
            def upload(self, data: bytes) -> None: ...
        model = EndpointModel.parse(Impl.upload)
        self.assertIn('data', [p.name for p in model.params.file_params])

    def test_bytes_or_str_input_is_file_param(self):
        class Impl:
            @websocket
            def upload(self, data: bytes | str) -> None: ...
        model = EndpointModel.parse(Impl.upload)
        self.assertIn('data', [p.name for p in model.params.file_params])

    def test_iterable_bytes_or_bytes_input_is_binary_stream(self):
        class Impl:
            @websocket
            def upload(self, data: Iterable[bytes] | bytes) -> None: ...
        model = EndpointModel.parse(Impl.upload)
        self.assertIsNotNone(model.params.binary_stream_param)
        self.assertEqual('data', model.params.binary_stream_param.name)

    def test_iterable_bytes_or_str_input_is_binary_stream(self):
        class Impl:
            @websocket
            def upload(self, data: Iterable[bytes] | str) -> None: ...
        model = EndpointModel.parse(Impl.upload)
        self.assertIsNotNone(model.params.binary_stream_param)
        self.assertEqual('data', model.params.binary_stream_param.name)

    def test_iterable_bytes_or_filelike_input_is_binary_stream(self):
        class Impl:
            @websocket
            def upload(self, data: Iterable[bytes] | FileLike) -> None: ...
        model = EndpointModel.parse(Impl.upload)
        self.assertIsNotNone(model.params.binary_stream_param)
        self.assertEqual('data', model.params.binary_stream_param.name)

    # Return types — ResultModel.parse calls _is_file_like_type, which treats
    # Iterable[bytes] the same as other binary types, so all are BinaryFile.

    def test_bytes_return_is_binary_file(self):
        class Impl:
            @endpoint
            def export(self, ckpt: str) -> bytes: ...
        model = EndpointModel.parse(Impl.export)
        self.assertEqual(ResultType.BinaryFile, model.result.type)

    def test_bytes_or_str_return_is_binary_file(self):
        class Impl:
            @endpoint
            def export(self, ckpt: str) -> bytes | str: ...
        model = EndpointModel.parse(Impl.export)
        self.assertEqual(ResultType.BinaryFile, model.result.type)

    def test_iterable_bytes_or_bytes_return_is_binary_file(self):
        class Impl:
            @endpoint
            def export(self, ckpt: str) -> Iterable[bytes] | bytes: ...
        model = EndpointModel.parse(Impl.export)
        self.assertEqual(ResultType.BinaryFile, model.result.type)

    def test_iterable_bytes_or_str_return_is_binary_file(self):
        class Impl:
            @endpoint
            def export(self, ckpt: str) -> Iterable[bytes] | str: ...
        model = EndpointModel.parse(Impl.export)
        self.assertEqual(ResultType.BinaryFile, model.result.type)

    def test_filelike_return_is_binary_file(self):
        class Impl:
            @endpoint
            def export(self, ckpt: str) -> FileLike: ...
        model = EndpointModel.parse(Impl.export)
        self.assertEqual(ResultType.BinaryFile, model.result.type)
