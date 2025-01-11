import datetime
from brainbox.deciders import OpenTTS, Collector
from brainbox.framework import FileIO, Loc
from brainbox import MediaLibrary, BrainBoxTask, BrainBoxApi
from pathlib import Path
from yo_fluq import Query

texts = {
    'train': ['computer' ,'how are you','how is it going' ,'make me a sandwich','set the timer for ten minutes'],
    'test': ["what's the weather", "remind me to wash dishes"]
}

if __name__ == '__main__':
    tags = []
    for voice in ['p256','p257']:
        for split in texts:
            for text in texts[split]:
                tags.append(dict(speaker=voice, split=split, text=text))
    pack = (
        Query.en(tags)
        .feed(Collector.FunctionalTaskBuilder(
            lambda z: BrainBoxTask.call(OpenTTS).voiceover(z['text'], speakerId=z['speaker'])
        ))
    )

    with BrainBoxApi.Test() as api:
        lib = api.execute(pack)
        api.download(lib, Path(__file__).parent/'test_media_library.zip', True)

