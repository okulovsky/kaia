from typing import *
from zoo.smart_home.switch_on_time import Space, create_algorithm, Settings
from kaia.infra.comm import Sql
from yo_fluq_ds import Query
from datetime import datetime, timedelta
from kaia.bro import debug_run
from functools import partial

def get_settings() -> Tuple[Settings, str]:
    try:
        from my.app_server.bro.settings import Settings
        settings = Settings()
        host = settings.host_machine
        real_settings = Settings().console_switch

    except:
        real_settings = None
        host = None
        pass
    return real_settings, host

def get_storage_and_messenger(host_machine):
    sql = Sql.test_file('debug_switch')
    storage = sql.storage()
    messenger = sql.messenger()
    return storage, messenger



if __name__ == '__main__':
    real_settings, host_machine = get_settings()

    schedule = (Query
                .loop(datetime(2022,1,1), timedelta(seconds=30), datetime(2022,1,2))
                .select(lambda z: z.time())
                .with_indices()
                .to_dictionary(lambda z: z.value, lambda z: z.key%2==0)
                )
    real_settings.schedule = schedule
    real_settings.plot_pause_in_ms = 10000
    real_settings.algorithm_update_in_ms = 10000
    real_settings.plot_pause_in_ms = 10000
    space = Space(real_settings.name)
    factory = partial(create_algorithm, space, False, real_settings)
    debug_run('test_switch_on_time', factory)