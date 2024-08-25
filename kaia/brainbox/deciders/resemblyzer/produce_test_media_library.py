import datetime

from kaia.brainbox.deciders import OpenTTSInstaller, OpenTTSSettings, OpenTTSApi
from kaia.brainbox.media_library import MediaLibrary
from kaia.infra import FileIO, Loc
import os
from pathlib import Path

texts = {
    'train': ['computer','how are you','how is it going','make me a sandwich','set the timer for ten minutes'],
    'test': ["what's the weather", "remind me to wash dishes"]
}

if __name__ == '__main__':
    installer = OpenTTSInstaller(OpenTTSSettings())
    api: OpenTTSApi = installer.run_in_any_case_and_create_api()
    records = []
    with Loc.create_temp_folder('resemblyzer_test_dataset_production') as folder:
        for split, sentences in texts.items():
            for i, sentence in enumerate(sentences):
                for voice in ['p256','p257']:
                    fname = f'{split}-{i}-{voice}.wav'
                    result = api.call(text=sentence, speakerId=voice)
                    FileIO.write_bytes(result, folder/fname)
                    record = MediaLibrary.Record(
                        filename=fname,
                        holder_location=folder,
                        timestamp=datetime.datetime.now(),
                        job_id='',
                        tags=dict(speaker=voice, split=split, index=i)
                    )
                    records.append(record)
        MediaLibrary(tuple(records)).save(Path(__file__).parent/'test_media_library.zip')
