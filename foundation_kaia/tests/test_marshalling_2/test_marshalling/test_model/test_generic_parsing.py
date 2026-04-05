from typing import TypeVar, Generic, Iterable
from dataclasses import dataclass
from unittest import TestCase

from foundation_kaia.marshalling_2 import service, endpoint, websocket, TestApi, ApiCall, Server, ServiceComponent, ServiceModel
from foundation_kaia.marshalling_2.marshalling.model import ResultType
from foundation_kaia.marshalling_2.serialization.handlers.type_handler import SerializationContext

T1 = TypeVar('T1')
T2 = TypeVar('T2')

@dataclass
class Input:
    s: str

@dataclass
class Output:
    i: int

@service
class MyService(Generic[T1, T2]):
    @endpoint
    def generic_argument(self, arg: T1) -> str:
        ...

    @endpoint
    def complex_generic_argument(self, arg: list[T1]) -> None:
        ...

    @endpoint
    def iterable_argument(self, arg: Iterable[T1]) -> None:
        ...

    @endpoint
    def generic_return(self) -> T2:
        ...

    @endpoint
    def complex_generic_return(self) -> list[T2]:
        ...

    @endpoint
    def iterable_return(self) -> Iterable[T2]:
        ...

    @websocket
    def stream_translate(self, arg: Iterable[T1]) -> Iterable[T2]:
        ...



class GenericTestCase(TestCase):
    def test_generic_service_parsing_input_output(self):
        svc = MyService[Input, Output]()
        model = ServiceModel.parse(svc)
        self.assertEqual(7, len(model.endpoints))

        eps = {ep.signature.name: ep for ep in model.endpoints}
        ctx = SerializationContext()

        # T1 is generic → must go to json_params regardless of concrete type,
        # so the server routing is stable across all generic instantiations.

        # generic_argument(arg: T1) — T1 resolves to Input (dataclass → json)
        ep = eps['generic_argument']
        self.assertEqual(0, len(ep.params.path_params))
        self.assertEqual(0, len(ep.params.query_params))
        self.assertEqual(1, len(ep.params.json_params))
        self.assertEqual('arg', ep.params.json_params[0].name)
        ser = ep.params.json_params[0].serializer
        self.assertEqual({'s': 'hello'}, ser.to_json(Input('hello'), ctx))
        self.assertEqual(Input('hello'), ser.from_json({'s': 'hello'}, ctx))

        # complex_generic_argument(arg: list[T1]) — list[Input] → json
        ep = eps['complex_generic_argument']
        self.assertEqual(0, len(ep.params.path_params))
        self.assertEqual(0, len(ep.params.query_params))
        self.assertEqual(1, len(ep.params.json_params))
        self.assertEqual('arg', ep.params.json_params[0].name)
        ser = ep.params.json_params[0].serializer
        self.assertEqual([{'s': 'a'}, {'s': 'b'}], ser.to_json([Input('a'), Input('b')], ctx))

        # iterable_argument(arg: Iterable[T1]) — Iterable[Input] → custom_stream_param
        ep = eps['iterable_argument']
        self.assertIsNone(ep.params.binary_stream_param)
        self.assertIsNotNone(ep.params.custom_stream_param)
        self.assertEqual('arg', ep.params.custom_stream_param.name)
        self.assertEqual({'s': 'x'}, ep.params.custom_stream_param.serializer.to_json(Input('x'), ctx))

        # generic_return() -> T2 — T2 resolves to Output → Json result
        ep = eps['generic_return']
        self.assertEqual(ResultType.Json, ep.result.type)
        self.assertEqual({'i': 42}, ep.result.serializer.to_json(Output(42), ctx))
        self.assertEqual(Output(42), ep.result.serializer.from_json({'i': 42}, ctx))

        # complex_generic_return() -> list[T2] — list[Output] → Json
        ep = eps['complex_generic_return']
        self.assertEqual(ResultType.Json, ep.result.type)
        self.assertEqual([{'i': 1}, {'i': 2}], ep.result.serializer.to_json([Output(1), Output(2)], ctx))

        # iterable_return() -> Iterable[T2] — Iterable[Output] → CustomIterable, item serializer = Output
        ep = eps['iterable_return']
        self.assertEqual(ResultType.CustomIterable, ep.result.type)
        self.assertEqual({'i': 7}, ep.result.serializer.to_json(Output(7), ctx))

        # stream_translate(arg: Iterable[T1]) -> Iterable[T2] — websocket roundtrip
        ep = eps['stream_translate']
        self.assertIsNone(ep.params.binary_stream_param)
        self.assertIsNotNone(ep.params.custom_stream_param)
        self.assertEqual('arg', ep.params.custom_stream_param.name)
        self.assertEqual({'s': 'y'}, ep.params.custom_stream_param.serializer.to_json(Input('y'), ctx))
        self.assertEqual(ResultType.CustomIterable, ep.result.type)
        self.assertEqual({'i': 3}, ep.result.serializer.to_json(Output(3), ctx))

    def test_generic_service_parsing_int_str(self):
        svc = MyService[int, str]()
        model = ServiceModel.parse(svc)
        self.assertEqual(7, len(model.endpoints))

        eps = {ep.signature.name: ep for ep in model.endpoints}
        ctx = SerializationContext()

        # generic_argument(arg: T1) — T1=int (primitive), but generic → must go to json_params
        ep = eps['generic_argument']
        self.assertEqual(0, len(ep.params.path_params))
        self.assertEqual(0, len(ep.params.query_params))
        self.assertEqual(1, len(ep.params.json_params))
        self.assertEqual('arg', ep.params.json_params[0].name)
        ser = ep.params.json_params[0].serializer
        self.assertEqual(42, ser.to_json(42, ctx))
        self.assertEqual(42, ser.from_json(42, ctx))

        # complex_generic_argument(arg: list[T1]) — list[int] → json
        ep = eps['complex_generic_argument']
        self.assertEqual(0, len(ep.params.path_params))
        self.assertEqual(0, len(ep.params.query_params))
        self.assertEqual(1, len(ep.params.json_params))
        self.assertEqual('arg', ep.params.json_params[0].name)
        ser = ep.params.json_params[0].serializer
        self.assertEqual([1, 2, 3], ser.to_json([1, 2, 3], ctx))

        # iterable_argument(arg: Iterable[T1]) — Iterable[int] → custom_stream_param
        ep = eps['iterable_argument']
        self.assertIsNone(ep.params.binary_stream_param)
        self.assertIsNotNone(ep.params.custom_stream_param)
        self.assertEqual('arg', ep.params.custom_stream_param.name)
        self.assertEqual(7, ep.params.custom_stream_param.serializer.to_json(7, ctx))

        # generic_return() -> T2 — T2=str (primitive), but generic → Json result
        ep = eps['generic_return']
        self.assertEqual(ResultType.Json, ep.result.type)
        self.assertEqual('hello', ep.result.serializer.to_json('hello', ctx))
        self.assertEqual('hello', ep.result.serializer.from_json('hello', ctx))

        # complex_generic_return() -> list[T2] — list[str] → Json
        ep = eps['complex_generic_return']
        self.assertEqual(ResultType.Json, ep.result.type)
        self.assertEqual(['a', 'b'], ep.result.serializer.to_json(['a', 'b'], ctx))

        # iterable_return() -> Iterable[T2] — Iterable[str] → StringIterable
        ep = eps['iterable_return']
        self.assertEqual(ResultType.StringIterable, ep.result.type)
        self.assertEqual('x', ep.result.serializer.to_json('x', ctx))

        # stream_translate(arg: Iterable[T1]) -> Iterable[T2] — Iterable[int] → Iterable[str]
        ep = eps['stream_translate']
        self.assertIsNone(ep.params.binary_stream_param)
        self.assertIsNotNone(ep.params.custom_stream_param)
        self.assertEqual('arg', ep.params.custom_stream_param.name)
        self.assertEqual(99, ep.params.custom_stream_param.serializer.to_json(99, ctx))
        self.assertEqual(ResultType.StringIterable, ep.result.type)
        self.assertEqual('y', ep.result.serializer.to_json('y', ctx))









