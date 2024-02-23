import json
import os

import requests

from zoo.smart_home.heating.space import Space
from zoo.smart_home.heating.algorithm import create_algorithm, HeatingSettings
from kaia.bro.core import BroServer
from kaia.infra.comm import Sql
from kaia.infra import Loc
from kaia.bro.amenities import gradio

def get_settings() -> Tuple[HeatingSettings, str]:
    try:
        from app.settings import Settings
        settings = Settings()
        host = settings.host_machine
        real_settings = Settings().kitchen_heating

    except:
        real_settings = None
        pass
    return real_settings, host_machine

def get_storage_and_messenger(host_machine):
    sql = Sql.test_file('debug_heating')
    storage = sql.storage()
    messenger = sql.messenger()

    data = requests.get(f"http://{host_machine}:7861/dump/heating/100").json()
    data = jsonpickle.loads(json.dumps(data))
    for d in data:
        storage.save('heating', d)
    return storage, messenger



if __name__ == '__main__':
    real_settings, host_machine = get_settings()
    space = Space(real_settings.name)
    real_settings.pause_in_ms = 10000
    real_settings.plot_pause_in_ms = 10000


    algorithm = create_algorithm(space, False, real_settings)
    sql = Sql.test_file('debug_heating')

    server = BroServer([algorithm], 1000)
    storage, messenger = get_storage_and_messenger(host_machine)
    server.run_in_multiprocess(storage, messenger)

    client = server.create_client(algorithm, storage, messenger)
    gradio_client = gradio.GradioClient(client, algorithm.presentation)
    gradio_client.generate_interface().launch()


