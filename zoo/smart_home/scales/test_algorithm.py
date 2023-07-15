from unittest import TestCase
from zoo.smart_home.scales.space import Space, ScalesStabilizer
from kaia.bro.core import BroAlgorithm, BroServer
from kaia.bro.amenities import ValuesInjector
import pandas as pd

def create_server(data):
    space = Space()
    algorithm = BroAlgorithm(
        space,
        [
            ValuesInjector(data),
            ScalesStabilizer(history_length=5),
        ],
    )
    server = BroServer([algorithm], iterations_limit=len(data)-1)
    return server, space

def create_test(*args):
    return [dict(readings=a) for a in args]

class ScalesTestCase(TestCase):
    def test_algorithm(self):
        data = create_test(
            [],
            [0, 0, 0],
            [100, 100, 100],
            [100, 100],
            [100],
            [121, 100, 100],
            [200,200,200,200,200]
        )
        server, space = create_server(data)
        server.run()
        df = space.as_data_frame()
        self.assertListEqual(
            [-1,-1,-1,100,100,-1,200],
            list(df.weight.fillna(-1).astype(int))
        )
        self.assertListEqual(
            [-1,-1,-1,100,-1,-1,200],
            list(df.weight_to_report.fillna(-1).astype(int))
        )
        log = server.last_track['scales']
        ldf = pd.DataFrame([c.__dict__ for c in log])
        print(ldf)

    def test_t(self):
        f = create_test
        print(type(f).__name__)