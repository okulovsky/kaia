from foundation_kaia.marshalling_2 import FileLike, service
from foundation_kaia.brainbox_utils import brainbox_endpoint


@service
class IResemblyzer:
    @brainbox_endpoint
    def vector(self, file: FileLike) -> list[float]:
        ...
