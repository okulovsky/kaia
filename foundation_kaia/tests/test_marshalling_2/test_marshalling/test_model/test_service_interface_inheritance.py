"""
Tests for endpoint detection when one @service interface inherits from another.

Scenario motivated by the question: if ModelDownloadingSupport inherits from
InstallingSupport, will ServiceModel.parse() detect endpoints from BOTH
IModelDownloadingSupport and IInstallingSupport?

The critical path in ServiceModel.parse():
  1. Walk MRO, stop at the first class that has _SERVICE_ATTR in its __dict__.
  2. Iterate vars(that_class) — direct members only, not inherited.

Consequence: if IChild(@service) extends IParent(@service), only IChild's own
@endpoint methods are discovered; IParent's endpoints are silently ignored.
"""
import unittest
from foundation_kaia.marshalling_2 import service, endpoint, ServiceModel


@service
class IParentService:
    @endpoint
    def parent_method(self) -> str:
        ...


@service
class IChildService(IParentService):
    @endpoint
    def child_method(self) -> str:
        ...


class CombinedImpl(IChildService):
    def parent_method(self) -> str:
        return "parent"

    def child_method(self) -> str:
        return "child"


class TestServiceInterfaceInheritance(unittest.TestCase):

    def test_child_endpoint_detected(self):
        """child_method defined directly on IChildService must always be found."""
        model = ServiceModel.parse(CombinedImpl())
        names = {ep.signature.name for ep in model.endpoints}
        self.assertIn('child_method', names)

    def test_parent_endpoint_detected(self):
        """parent_method lives on IParentService, NOT on IChildService.

        ServiceModel.parse() stops at the first @service in MRO (IChildService)
        and iterates vars(IChildService), which does NOT include parent_method.
        This test FAILS with the current implementation, confirming that
        inheriting @service interfaces does NOT compose their endpoints.
        """
        model = ServiceModel.parse(CombinedImpl())
        names = {ep.signature.name for ep in model.endpoints}
        self.assertIn('parent_method', names)

    def test_both_endpoints_present(self):
        """Combined implementation must expose exactly 2 endpoints."""
        model = ServiceModel.parse(CombinedImpl())
        self.assertEqual(2, len(model.endpoints))
