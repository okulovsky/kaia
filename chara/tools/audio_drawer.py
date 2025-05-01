from .drawer import Drawer
import ipywidgets
from brainbox import File
from yo_fluq import *



class AudioDrawer(Drawer[bytes]):
    def __init__(self, records, columns=5):
        super().__init__(records)
        self.columns = columns

    def _to_one_widget(self, objects):
        widgets = Query.en(objects).select(
            lambda z: ipywidgets.VBox([ipywidgets.Audio(value=z[0], autoplay=False), ipywidgets.Label(z[1])]))
        if self.columns is not None:
            widgets = widgets.feed(fluq.partition_by_count(self.columns)).select(ipywidgets.HBox)
        return ipywidgets.VBox(list(widgets))

    def _retrieve_postprocess(self, s):
        if isinstance(s, File):
            return s.content
        return s