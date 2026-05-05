import os
import shutil

from chara.common import Chara
import json
from chara.nlu.datasets.voice_dataset.voice_dataset_pipeline import VoiceDatasetPipeline
from chara.voice_clone.common import CosyVoiceTrain, CosyVoiceInference
from chara.voice_clone.utilities.transcriber_utility import transcribe_files_in_folder
from pathlib import Path
import subprocess
import tqdm

if __name__ == '__main__':
    datasets = Chara.Apis.content_folder / 'nlu/datasets'
    text_dataset = json.loads((datasets / 'text-dataset.json').read_text())
    voice_folder = Chara.Apis.datasets_folder / 'nlu/voices_dataset'
    #transcribe_files_in_folder(voice_folder, Chara.Apis.brainbox_api)
    voices = list(voice_folder.glob('*.wav'))
    texts = list(set([t['text'] for t in text_dataset]))[:500]

    pipeline = VoiceDatasetPipeline(
        voices,
        CosyVoiceTrain(),
        CosyVoiceInference(True),
        texts
    )

    output = datasets / 'to_zip'
    shutil.rmtree(output, ignore_errors=True)
    os.makedirs(output)
    records = []
    for wav in tqdm.tqdm(Chara.previous.result):
        speaker = Path(wav.metadata['model_source']).name
        language = speaker.split('-')[0]
        filename = wav.name + '.aac'
        text = wav.metadata['text']
        records.append(dict(
            speaker=speaker,
            language=language,
            text=text,
            filename=filename
        ))
        subprocess.call(['ffmpeg', '-loglevel', 'quiet', '-nostats', '-i', wav.path, output / filename])
    (output / 'samples.json').write_text(json.dumps(records, indent=2, ensure_ascii=False))
