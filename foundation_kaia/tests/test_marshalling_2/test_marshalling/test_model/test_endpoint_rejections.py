from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar
from unittest import TestCase

from foundation_kaia.marshalling_2.marshalling.model import EndpointModel, endpoint, websocket, FileLike
from foundation_kaia.marshalling_2 import service, ServiceModel


@dataclass
class Data:
    value: int


class TestEndpointRejections(TestCase):

    # --- two stream params ---

    def test_two_stream_params_rejected_ws(self):
        """Having two stream parameters is rejected for WebSocket endpoints."""
        class BadImpl:
            @websocket(verify_abstract=False)
            def bad(self, a: Iterable[bytes], b: Iterable[str]) -> str:
                return ""

        with self.assertRaises(ValueError):
            EndpointModel.parse(BadImpl.bad)

    def test_two_binary_stream_params_rejected_http(self):
        """Having two Iterable[bytes] parameters is rejected for HTTP endpoints too."""
        class BadImpl:
            @endpoint(verify_abstract=False)
            def bad(self, a: Iterable[bytes], b: Iterable[bytes]) -> str:
                return ""

        with self.assertRaises(ValueError):
            EndpointModel.parse(BadImpl.bad)

    # --- bare Iterable (no type argument) ---

    def test_bare_iterable_rejected(self):
        """Iterable without a type argument is not a valid endpoint parameter."""
        class BadImpl:
            @endpoint(verify_abstract=False)
            def bad(self, data: Iterable) -> None:
                pass

        with self.assertRaises(ValueError):
            EndpointModel.parse(BadImpl.bad)

    # --- HTTP: stream cannot be combined with other body params ---

    def test_http_stream_with_json_body_rejected(self):
        """HTTP endpoints cannot combine a binary stream with a JSON body parameter."""
        class BadImpl:
            @endpoint(verify_abstract=False)
            def bad(self, data: Iterable[bytes], p: Data) -> None:
                pass

        with self.assertRaises(ValueError):
            EndpointModel.parse(BadImpl.bad)

    def test_http_stream_with_file_rejected(self):
        """HTTP endpoints cannot combine a binary stream with a FileLike parameter."""
        class BadImpl:
            @endpoint(verify_abstract=False)
            def bad(self, data: Iterable[bytes], f: FileLike) -> None:
                pass

        with self.assertRaises(ValueError):
            EndpointModel.parse(BadImpl.bad)

    # --- HTTP: streaming input + streaming output ---

    def test_http_cannot_have_streaming_input_and_output(self):
        """HTTP endpoints must not have both streaming input and streaming output;
        the WebSocket protocol should be used instead."""
        class HttpRoundtripImpl:
            @endpoint(verify_abstract=False)
            def roundtrip(self, data: Iterable[bytes]) -> Iterable[bytes]:
                yield from data

        with self.assertRaises(ValueError) as ctx:
            EndpointModel.parse(HttpRoundtripImpl.roundtrip)
        self.assertIn("WebSocket", str(ctx.exception))

    # --- unbound TypeVar in endpoint parameter ---

    def test_unbound_typevar_raises(self):
        """ServiceModel.parse with an unbound TypeVar must raise, not silently fail at runtime."""
        T = TypeVar('T')

        @service
        class IGeneric(Generic[T]):
            @endpoint
            def do(self, value: T) -> None: ...

        class ConcreteGeneric(IGeneric[T]):
            def do(self, value: T) -> None: ...

        with self.assertRaises(TypeError) as ctx:
            ServiceModel.parse(ConcreteGeneric())
        self.assertIn('T', str(ctx.exception))

    def test_bound_typevar_does_not_raise(self):
        """ServiceModel.parse with a concrete type argument must succeed."""
        T = TypeVar('T')

        @service
        class IGeneric(Generic[T]):
            @endpoint
            def do(self, value: T) -> None: ...

        class ConcreteGeneric(IGeneric[T]):
            def do(self, value: T) -> None: ...

        model = ServiceModel.parse(ConcreteGeneric[int]())
        self.assertEqual(1, len(model.endpoints))

    # --- verify_abstract: real body rejected at decoration time ---

    def test_endpoint_with_real_body_rejected(self):
        """@endpoint with verify_abstract=True (default) rejects a method with a real body."""
        with self.assertRaises(TypeError):
            @endpoint
            def func(self) -> str:
                return "real"

    def test_websocket_with_real_body_rejected(self):
        """@websocket with verify_abstract=True (default) rejects a method with a real body."""
        with self.assertRaises(TypeError):
            @websocket
            def func(self) -> str:
                return "real"

