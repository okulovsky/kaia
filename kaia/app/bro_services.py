from .app import IKaiaService, KaiaAppConfig
from ..bro.core import BroServer, BroClient, StorageClientDataProvider
from ..bro.amenities.gradio import GradioClient
import gradio as gr

class ControlBroService(IKaiaService):
    def __init__(self, server: BroServer):
        self.server = server

    def run(self, app_config: KaiaAppConfig):
        self.server.run(app_config.comm.storage(), app_config.comm.messenger())


class GradioBroService(IKaiaService):
    def __init__(self, server: BroServer):
        self.server = server

    def run(self, app_config: KaiaAppConfig):
        demo = GradioClient.generate_server_interface(self.server, app_config.comm.storage(), app_config.comm.messenger())
        demo.queue().launch(ssl_verify=False, server_name='0.0.0.0', share=False)








