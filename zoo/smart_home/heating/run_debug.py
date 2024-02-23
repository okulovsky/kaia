from zoo.smart_home.heating.space import Space
from zoo.smart_home.heating.algorithm import create_algorithm, HeatingSettings
from zoo.smart_home.heating.heating_plan import HeatingPlan, HeatingInterval
from kaia.bro.core import BroServer
from kaia.infra.comm import Sql
from kaia.bro.amenities import gradio
from datetime import datetime, timedelta, time

def create_debug_plan(mult):
    now = datetime.now()
    now = datetime(now.year, now.month, now.day, now.hour, now.minute)
    span = timedelta(minutes=mult)
    ints = []
    tm = now
    cnt = int(timedelta(hours=24)/span)
    for i in range(cnt):
        ints.append(HeatingInterval(tm.time(), (tm+span).time(), 22))
        tm+=2*span
    return HeatingPlan(f'plan_{mult}', 18, tuple(ints))




if __name__ == '__main__':
    space = Space('test')
    settings = HeatingSettings(
        '',
        '',
        100,
        1000,
        1000,
        [
            create_debug_plan(1),
            create_debug_plan(2),
            create_debug_plan(3)
        ])
    algorithm = create_algorithm(space, True, settings)
    sql = Sql.test_file('debug_heating')

    server = BroServer([algorithm], 0)
    storage = sql.storage()
    messenger = sql.messenger()
    server.run_in_multiprocess(storage, messenger)

    client = server.create_client(algorithm, storage, messenger)
    gradio_client = gradio.GradioClient(client, algorithm.presentation)
    gradio_client.generate_interface().launch()