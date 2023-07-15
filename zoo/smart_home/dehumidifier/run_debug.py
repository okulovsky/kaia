from zoo.smart_home.dehumidifier.space import Space
from zoo.smart_home.dehumidifier.algorithm import create_algorithm
from kaia.bro.core import BroServer
from kaia.infra.comm import Sql
from kaia.bro.amenities import gradio
from zoo.smart_home.dehumidifier.plot import draw


if __name__ == '__main__':
    space = Space()
    algorithm = create_algorithm(space, True, None)
    sql = Sql.file('debug_dehumidifier', True)
    server = BroServer([algorithm], sql.storage(), sql.messenger(), 100)
    server.run_in_multiprocess()

    client = server.get_client(space.get_name())
    gradio_client = gradio.GradioClient(client, draw, 1,1,1)
    gradio_client.generate_interface().launch()