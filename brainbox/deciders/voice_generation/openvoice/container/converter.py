from openvoice.api import ToneColorConverter
import torch
from openvoice import se_extractor

class Converter:
    def __init__(self):
        CKPT_CONVERTER = 'checkpoints/converter'
        self.device  = "cuda:0" if torch.cuda.is_available() else "cpu"

        self.tone_color_converter = ToneColorConverter(
            f'{CKPT_CONVERTER}/config.json',
            device=self.device
        )
        self.tone_color_converter.load_ckpt(f'{CKPT_CONVERTER}/checkpoint.pth')

    def convert(self, path):
        source_se, _ = se_extractor.get_se(
            path,
            self.tone_color_converter,
            vad=True
        )
        return source_se



