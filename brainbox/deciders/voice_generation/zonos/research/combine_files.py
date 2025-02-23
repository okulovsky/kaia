from brainbox import BrainBox
from brainbox.deciders import Ffmpeg
from yo_fluq import *
from pathlib import Path

if __name__ == '__main__':
    files = Query.folder(Path(__file__).parent.parent.parent/'piper_training/files', '*.wav').to_list()
    print(files)
    with BrainBox.Api.Test() as api:
        result = api.execute(BrainBox.Task.call(Ffmpeg).concat(files, '.mp3'))
        api.download(result, Path(__file__).parent/'lina.mp3')
