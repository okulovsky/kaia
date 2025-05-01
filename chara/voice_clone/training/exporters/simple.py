from brainbox import BrainBox
from ...upsampling import UpsamplingItem
from .exporter import IExporter, ExportItem

class SimpleExporter(IExporter):
    def __init__(self, api: BrainBox.Api):
        self.api = api

    def export(self, item: UpsamplingItem) -> ExportItem:
        return ExportItem(
            item.voiceover_file,
            item.voiceover_tags['character'],
            item.voiceover_tags['text'],
            item.vosk[-1]['end'] - item.vosk[0]['start']
        )

    def get_content(self, item: ExportItem) -> bytes:
        return self.api.open_file(item.filename).content


