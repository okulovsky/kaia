from .core import BroServer
from .amenities.gradio import GradioClient
from ..infra.comm import IStorage, IMessenger
import gradio as gr

class ControlBroService:
    def __init__(self, server: BroServer, storage: IStorage, messenger: IMessenger):
        self.server = server
        self.storage = storage
        self.messenger = messenger

    def __call__(self):
        self.server.run(self.storage, self.messenger)


class GradioBroService:
    def __init__(self, server: BroServer, storage: IStorage, messenger: IMessenger):
        self.server = server
        self.storage = storage
        self.messenger = messenger

    def __call__(self):
        demo = GradioClient.generate_server_interface(self.server, self.storage, self.messenger)
        demo.queue().launch(ssl_verify=False, server_name='0.0.0.0', share=False)








