from typing import TypeVar, Generic, Iterable
from dataclasses import dataclass
from unittest import TestCase

from foundation_kaia.marshalling import (
    service, endpoint, websocket, TestApi, ApiCall, Server, ServiceComponent
)

T1 = TypeVar('T1')
T2 = TypeVar('T2')

@service
class MyService(Generic[T1, T2]):
    def __init__(self, t2_factory):
        self.t2_factory = t2_factory

    @endpoint(verify_abstract=False)
    def generic_argument(self, arg: T1) -> str:
        return str(arg)

    @endpoint(verify_abstract=False)
    def complex_generic_argument(self, arg: list[T1]) -> None:
        return len(arg)

    @endpoint(verify_abstract=False)
    def iterable_argument(self, arg: Iterable[T1]) -> None:
        return len(list(arg))

    @endpoint(verify_abstract=False)
    def generic_return(self) -> T2:
        return self.t2_factory()

    @endpoint(verify_abstract=False)
    def complex_generic_return(self) -> list[T2]:
        return [self.t2_factory()]*3

    @endpoint(verify_abstract=False)
    def iterable_return(self) -> Iterable[T2]:
        return [self.t2_factory()]*3

    @websocket(verify_abstract=False)
    def stream_translate(self, arg: Iterable[T1]) -> Iterable[T2]:
        for e in arg:
            yield self.t2_factory()
            yield self.t2_factory()

@dataclass
class Input:
    s: str

@dataclass
class Output:
    i: int

class MyServer(Server):
    def __init__(self, service: MyService):
        super().__init__(4522, ServiceComponent(service))

class Api1(MyService[Input, Output]):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, MyService[Input, Output])

class Api2(MyService[int, str]):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, MyService[int, str])


def _make_output() -> Output:
    return Output(10)


class GenericTestCase(TestCase):
    def test_service_input_output(self):
        service = MyService[Input, Output](_make_output)
        with TestApi[Api1](Api1, MyServer(service)) as api:

            # generic_argument(arg: T1=Input) -> str
            result = api.generic_argument(Input('test'))
            self.assertEqual("Input(s='test')", result)
            self.assertEqual({'arg': {'s': 'test'}}, api.generic_argument.last_request.content.json)
            self.assertEqual("Input(s='test')", api.generic_argument.last_raw_response)

            # generic_return() -> T2=Output
            result = api.generic_return()
            self.assertEqual(Output(10), result)
            self.assertEqual({}, api.generic_return.last_request.content.json)
            self.assertEqual({'i': 10}, api.generic_return.last_raw_response)

            # complex_generic_return() -> list[T2=Output]
            result = api.complex_generic_return()
            self.assertEqual([Output(10)] * 3, result)
            self.assertEqual({}, api.complex_generic_return.last_request.content.json)
            self.assertEqual([{'i': 10}] * 3, api.complex_generic_return.last_raw_response)

            # stream_translate(Iterable[T1=Input]) -> Iterable[T2=Output]  (WebSocket)
            # each input item triggers two output yields
            gen = api.stream_translate(iter([Input('a'), Input('b')]))
            self.assertEqual({}, api.stream_translate.last_request.content.json)
            result = list(gen)  # consume — also populates last_raw_response
            self.assertEqual([Output(10)] * 4, result)
            self.assertEqual([{'i': 10}] * 4, api.stream_translate.last_raw_response)










