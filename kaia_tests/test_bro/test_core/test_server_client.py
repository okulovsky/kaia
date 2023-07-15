from unittest import TestCase

import pandas as pd

from kaia.infra.comm import Sql
from kaia.bro.core import BroAlgorithm, BroServer
from kaia.bro.sandbox import SinSpace, sin_algorithm
from kaia.bro import amenities as am
from dataclasses import dataclass
import math
import time
import numpy as np


class ServerClientTestCase(TestCase):
    def test_client_server(self):
        space = SinSpace()
        algorithm = space.create_algorithm()

        file = 'sample'
        conn = Sql.file(file, True)
        storage = conn.storage()
        messenger = conn.messenger()
        server = BroServer([algorithm],pause_in_milliseconds=50)
        server.run_in_multiprocess(storage, messenger)

        client = server.create_client(algorithm, storage, messenger)
        time.sleep(0.5)
        client.set_field(space.amplitude, 2)
        client.set_field(space.frequency, 3)
        time.sleep(0.5)
        client.set_field(space.amplitude, 5)
        client.disable()
        time.sleep(0.5)
        client.set_field(space.amplitude, 3)
        client.enable()
        time.sleep(0.5)
        client.set_field(space.time, -1)
        self.assertRaises(ValueError, lambda: client.check_last_field_validation())
        client.set_field(space.amplitude, 4)
        time.sleep(0.5)

        self.assertEqual(0, client.space.as_data_frame().shape[0])
        data = client.data_provider.pull()

        df = pd.DataFrame(data)
        df['control'] = df.amplitude * np.sin(df.frequency * df.time)
        self.assertTrue( ((df.control-df.signal).abs()<0.01).all() )


        print(storage.load('bro_server_stats'))

        print(df.groupby('amplitude').size())
        for i in [1,2,3,4]:
            n = df.loc[df.amplitude==i].shape[0]
            self.assertGreater(n, 5)
            self.assertLess(n, 12)

        client.terminate()




