import json

from TTS.api import TTS
import torch
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TTSInfo:
    tts: TTS
    device: str
    is_custom_model: bool


def _load_custom_model(folder, filename, device):
    with open(folder / (filename + '.json')) as file:
        spec = json.load(file)
    spec['model_args']['d_vector_file'] = [str(folder / (filename + '.speakers.pth'))]
    with open(folder / (filename + '.fixed.json'), 'w') as file:
        json.dump(spec, file)
    tts = TTS(model_path=folder / filename, config_path=folder / (filename + '.fixed.json')).to(device)
    return tts

def load_tts(model_name) -> TTSInfo:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if model_name.startswith('tts_models'):
        api = TTS("")
        api.manager.output_prefix = '/resources/builtin'
        api.load_tts_model_by_name(model_name)
        tts = api.to(device)
        return TTSInfo(tts, device, False)
    if model_name.startswith('custom/'):
        folder = Path('/resources/custom')
        filename = model_name.replace('custom/','')
        tts = _load_custom_model(folder, filename, device)
        return TTSInfo(tts, device, True)
    else:
        raise ValueError('Not yet supported')