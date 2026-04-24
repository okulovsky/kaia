from foundation_kaia.marshalling import service, endpoint
from .dto import Batches, BatchSummary


@service
class IBatchesService:
    @endpoint(method='GET')
    def get_batches(self, offset: int | None = None, size: int | None = None) -> Batches:
        """Returns paginated batch records."""
        ...

    @endpoint(method='POST')
    def cancel_batch(self, batch_id: str) -> None:
        """Cancels all pending jobs in a batch."""
        ...

    @endpoint(method='GET')
    def get_batch_progress(self, batch_id: str) -> BatchSummary:
        """Returns a progress summary for a batch."""
        ...

