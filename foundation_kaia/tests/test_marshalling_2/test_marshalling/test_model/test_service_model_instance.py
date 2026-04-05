"""
Regression test for ServiceModel.parse called with a service *instance*
whose methods override the interface without the @endpoint decorator.

Before the fix, `bound = getattr(service_instance, name)` returned the
concrete override (no _ENDPOINT_ATTR), so EndpointModel.parse returned None
and no routes were registered → 404 on every endpoint.
"""
import unittest
from dataclasses import dataclass
from foundation_kaia.marshalling_2 import service, endpoint, ServiceModel


@dataclass
class Payload:
    value: int


@service
class IMyService:
    @endpoint
    def compute(self, x: int, y: int) -> int:
        ...

    @endpoint
    def process(self, data: Payload) -> Payload:
        ...


class MyServiceImpl(IMyService):
    """Concrete implementation — methods have no @endpoint decorator."""

    def compute(self, x: int, y: int) -> int:
        return x + y

    def process(self, data: Payload) -> Payload:
        return Payload(data.value * 2)


class TestServiceModelParseInstance(unittest.TestCase):

    def test_parse_interface_finds_all_endpoints(self):
        """Parsing the interface class itself works (baseline)."""
        model = ServiceModel.parse(IMyService)
        self.assertEqual(2, len(model.endpoints))

    def test_parse_instance_finds_all_endpoints(self):
        """Parsing a concrete instance must find the same endpoints as the interface."""
        model = ServiceModel.parse(MyServiceImpl())
        self.assertEqual(2, len(model.endpoints))

    def test_parse_instance_endpoint_names(self):
        names = {ep.signature.name for ep in ServiceModel.parse(MyServiceImpl()).endpoints}
        self.assertEqual({'compute', 'process'}, names)

    def test_parse_instance_service_model_set_on_endpoints(self):
        """service_model back-reference must be set on every endpoint."""
        model = ServiceModel.parse(MyServiceImpl())
        for ep in model.endpoints:
            self.assertIs(model, ep.service_model)

    def test_parse_instance_endpoint_address_includes_service_name(self):
        """endpoint_address should be <service>/<endpoint>, not just <endpoint>."""
        model = ServiceModel.parse(MyServiceImpl())
        eps = {ep.signature.name: ep for ep in model.endpoints}
        self.assertEqual('my-service/compute', eps['compute'].endpoint_address)
        self.assertEqual('my-service/process', eps['process'].endpoint_address)
