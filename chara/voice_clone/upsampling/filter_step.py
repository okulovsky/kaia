from brainbox.flow import IStep
from .upsampling_item import UpsamplingItem

class FilterStep(IStep):
    def process(self, history: list[UpsamplingItem], current: list[UpsamplingItem]):
        seen = {(item.text, item.voice_cloner.get_voice_cloner_key())for item in history if item.selected}
        return [item for item in current if (item.text, item.voice_cloner.get_voice_cloner_key()) not in seen]