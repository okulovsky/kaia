from .core import BroServer, StorageClientDataProvider, BroClient
from .amenities.gradio import GradioClient
from ..infra.comm import Sql
from ..infra.app import KaiaApp

class _DebugService:
    def __init__(self, algorithm_factory, storage, messenger):
        self.algorithm_factory = algorithm_factory
        self.storage = storage
        self.messenger = messenger

    def __call__(self):
        algorithm = self.algorithm_factory()
        server = BroServer([algorithm], 1000)
        server.run(self.storage, self.messenger)



def debug_run(name, algorithm_factory):
    sql = Sql.test_file(name)
    storage = sql.storage()
    messenger = sql.messenger()
    service = _DebugService(algorithm_factory, storage, messenger)
    app = KaiaApp()
    app.add_subproc_service(service)
    app.run_services_only()

    algorithm = algorithm_factory()
    puller = StorageClientDataProvider(
        algorithm.space.get_name(),
        storage,
        algorithm.max_history_length)
    client = BroClient(algorithm.space, puller, messenger)
    gradio_client = GradioClient(client, algorithm.presentation)
    gradio_client.generate_interface().launch()