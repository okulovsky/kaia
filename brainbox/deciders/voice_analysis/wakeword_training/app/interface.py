from collections.abc import Iterable

from foundation_kaia.brainbox_utils import (
    BrainboxReportItem,
    brainbox_endpoint,
    brainbox_websocket,
)
from foundation_kaia.marshalling import JSON, FileLike, service


@service
class IWakewordTraining:
    @brainbox_endpoint
    def readiness(self) -> JSON: ...

    @brainbox_endpoint
    def describe(self, training_id: str) -> JSON: ...

    @brainbox_websocket
    def train(  # type: ignore[empty-body]
        self,
        training_id: str,
        parameters: JSON,
        expected_dataset: JSON,
        dataset: FileLike,
    ) -> Iterable[BrainboxReportItem[JSON]]: ...

    @brainbox_endpoint
    def export(self, result: JSON) -> FileLike:  # type: ignore[empty-body]
        ...
