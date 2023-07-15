from typing import *
import gradio as gr
from ...core import BroClient, Slot, RangeInput, BoolInput, BroAlgorithmPresentation, BroServer
from yo_fluq_ds import *
import pandas as pd
from .updater import Updater
from .configurer import Configurer
from ....infra import Loc
from datetime import datetime



class GradioClient:
    def __init__(self,
                 client: BroClient,
                 presentation: BroAlgorithmPresentation
                 ):
        self.client = client
        self.presentation = presentation

        self.pull = Updater(self.presentation.data_update_in_milliseconds/1000, self._pull)
        self.html = Updater(self.presentation.data_update_in_milliseconds/1000, self._html)
        self.plot = Updater(self.presentation.plot_update_in_milliseconds/1000, self._plot)

        self.configurer = Configurer(
            client.space.get_name(),
            self.pull,
            client.messenger,
            client.space.get_slots()
        )


    def _pull(self):
        return self.client.data_provider.pull()

    def _html(self):
        data = self.pull()
        if data is None or len(data)==0:
            return ''
        current = data[-1]
        html = (Query
                .dict(current)
                .where(lambda z: self.client.space.get_slot(z.key).shown)
                .select(lambda z: f'<tr><td>{z.key}</td><td>{z.value}</tr>')
                .prepend('<table>').append('</table>')
                .feed(lambda z: '\n'.join(z))
               )
        return html

    def _plot(self):
        if self.presentation.plot_function is None:
            return None
        data = self.pull()
        if data is None or len(data) == 0:
            return None
        df = pd.DataFrame(data)
        return self.presentation.plot_function(df)

    def generate_interface(self):
        with gr.Blocks() as demo:
            self.generate_interface_inner()
        return demo.queue()

    def generate_interface_inner(self):
        if self.presentation.plot_function is not None:
            self.cm_plot = gr.Plot(value=self.plot, every=self.presentation.plot_update_in_milliseconds/1000)
        with gr.Row():
            with gr.Column():
                self.cm_html = gr.HTML(value=self.html, every=self.presentation.data_update_in_milliseconds/1000)
                stash_name = gr.Textbox(value='', label='Report name')
                stash = gr.Button('Report problem')
                stash.click(self._cm_stash, inputs=[stash_name], outputs=[])
            with gr.Column():
                self.configurer.generate_interface()

    def _cm_stash(self, report_name):
        path = Loc.data_folder/'debug'/f'{self.client.space.get_name()}-{report_name}-{datetime.now()}.parquet'
        data = self.pull()
        if data is not None:
            df = pd.DataFrame(data)
            df.to_parquet(path)


    @staticmethod
    def generate_server_interface(server: BroServer, storage, messenger):
        with gr.Blocks() as demo:
            with gr.Tabs():
                for algorithm in server.algorithms:
                    with gr.Tab(algorithm.space.get_name()):
                        client = server.create_client(algorithm, storage, messenger)
                        gradio_client = GradioClient(
                            client,
                            algorithm.presentation
                        )
                        gradio_interface = gradio_client.generate_interface_inner()
        return demo.queue()
