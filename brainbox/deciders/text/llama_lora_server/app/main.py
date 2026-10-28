import sys
from foundation_kaia.marshalling import Server, ServiceComponent
from service import LlamaLoraServerService

BRAINBOX_PORT = 8080


if __name__ == '__main__':
    model_id = sys.argv[1]
    server = Server(
        BRAINBOX_PORT,
        ServiceComponent(LlamaLoraServerService(model_id)),
    )
    server.create_web_app_entry_point().run()
