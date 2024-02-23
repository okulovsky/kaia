from .core import BroServer
from .amenities.gradio import GradioClient
from ..infra.comm import IStorage, IMessenger
import flask
import pandas as pd

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


class DataAccessService:
    def __init__(self, server: BroServer, storage: IStorage, port: int):
        self.server = server
        self.storage = storage
        self.port = port

    def __call__(self):
        self.app = flask.Flask('brainbox')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        #self.app.add_url_rule('/dump/<space>/<count>', view_func=self.dump, methods=['GET'])
        self.app.add_url_rule('/df/<space>/<count>', view_func=self.df, methods=['GET'])
        self.app.run('0.0.0.0', self.port)

    def index(self):
        lengths = [10, 100, 500, 1000]
        buffer = ['<table><tr><td>Algorithm</td>']
        for l in lengths:
            buffer.append(f'<td>{l}</td>')
        buffer.append('</tr>')
        for alg in self.server.algorithms:
            name = alg.space.get_name()
            buffer.append(f'<tr><td>{name}</td>')
            for l in lengths:
                buffer.append('<td>')
                buffer.append(f'<a href="/df/{name}/{l}">df</a><br>')
                #buffer.append(f'<a href="/dump/{name}/{l}">dump</a>')
                buffer.append('</td>')
            buffer.append('</tr>')
        buffer.append("</table>")
        return ''.join(buffer)

    def df(self, space: str, count: int):
        data = self.storage.load(space, int(count), False)
        for d in data:
            for c in list(d.keys()):
                if len(str(d[c]))>100:
                    del d[c]
        df = pd.DataFrame(data)
        return df.to_html()









